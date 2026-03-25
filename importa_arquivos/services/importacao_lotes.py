"""
Serviço de validação e processamento de arquivos de lote (SIGPEC).

O arquivo é um TXT delimitado por ';' com header fixo:
LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC

Nota: CHAVE_INSCRITO é ignorada — equivale ao codigo_inscricao já existente no candidato.
"""
import csv
import io
import logging
from typing import Any

from importa_arquivos.services.exceptions import (
    ArquivoLotesVazioException,
    CampoObrigatorioLotesException,
    ColunaCSVInvalidaException,
    LeituraCSVException,
    MultiplosLotesException,
)

logger = logging.getLogger(__name__)

COLUNAS_ESPERADAS = {'LOTE', 'EMPRESA', 'VAGA', 'IDENTIFICACAO', 'CHAVE_INSCRITO', 'NUMFUNC', 'NUMVINC'}


def validar_txt_lotes(arquivo) -> list[dict[str, Any]]:
    """
    Lê e valida o arquivo TXT de lotes.

    - Delimitador: ';'
    - Header fixo: LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC
    - Linhas vazias são ignoradas
    - O trailing ';' nas linhas de dados gera um campo vazio extra, que é ignorado
    - Todos os registros devem possuir o mesmo valor na coluna LOTE

    Retorna lista de dicts com as chaves em minúsculo correspondendo aos campos do lote.
    Lanca excecoes de dominio de importacao em caso de erro de validacao.
    """
    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode('utf-8-sig')
    except Exception as exc:
        raise LeituraCSVException(
            mensagem='Nao foi possivel ler o arquivo de lotes.',
            detalhes=f'Detalhes tecnicos: {exc}',
        ) from exc

    if not text or not text.strip():
        raise ArquivoLotesVazioException(
            mensagem='O arquivo de lotes esta vazio.',
            detalhes='Arquivo sem conteudo util para processamento.',
        )

    reader = csv.DictReader(io.StringIO(text), delimiter=';')

    headers_csv = {h for h in (reader.fieldnames or []) if h}
    colunas_faltando = COLUNAS_ESPERADAS - headers_csv
    if colunas_faltando:
        raise ColunaCSVInvalidaException(
            mensagem='Cabecalho invalido para importacao de lotes.',
            detalhes=(
                f'Colunas ausentes: {sorted(colunas_faltando)}. '
                f'Esperado: {sorted(COLUNAS_ESPERADAS)}'
            ),
        )

    registros: list[dict[str, Any]] = []
    lotes_encontrados: set[str] = set()
    for row in reader:
        # Ignorar linhas completamente vazias
        valores = [v for k, v in row.items() if k and v is not None and str(v).strip()]
        if not valores:
            continue

        lote = row.get('LOTE', '').strip()
        if not lote:
            identificacao = row.get('IDENTIFICACAO', '').strip()
            raise CampoObrigatorioLotesException(
                mensagem="Campo obrigatorio 'LOTE' nao pode estar vazio.",
                detalhes=f'Linha {reader.line_num}: coluna LOTE obrigatoria e nao pode estar vazia.',
                erros_por_linha=[
                    {
                        'linha': reader.line_num,
                        'identificacao': identificacao,
                        'mensagem': "Campo obrigatorio 'LOTE' nao pode estar vazio.",
                    }
                ],
            )

        lotes_encontrados.add(lote)

        registros.append({
            'lote': lote,
            'empresa': row.get('EMPRESA', '').strip(),
            'vaga': row.get('VAGA', '').strip(),
            'identificacao': row.get('IDENTIFICACAO', '').strip(),
            'chave_inscrito': row.get('CHAVE_INSCRITO', '').strip(),
            'numfunc': row.get('NUMFUNC', '').strip(),
            'numvinc': row.get('NUMVINC', '').strip(),
        })

    if not registros:
        raise ArquivoLotesVazioException(
            mensagem='O arquivo nao contem registros validos.',
            detalhes='Apenas cabecalho ou linhas vazias foram encontradas.',
        )

    if len(lotes_encontrados) > 1:
        raise MultiplosLotesException(
            mensagem="Arquivo invalido: todos os valores da coluna 'LOTE' devem ser iguais.",
            detalhes=f'Encontrados: {sorted(lotes_encontrados)}',
        )

    logger.info('validar_txt_lotes: %d registros lidos do arquivo.', len(registros))
    return registros

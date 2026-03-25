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

from pydantic import BaseModel, ValidationError, field_validator

from importa_arquivos.services.erros import captura_erros_importacao
from importa_arquivos.services.exceptions import (
    ArquivoLotesVazioException,
    ColunaCSVInvalidaException,
    LeituraCSVException,
)

logger = logging.getLogger(__name__)

COLUNAS_ESPERADAS = {'LOTE', 'EMPRESA', 'VAGA', 'IDENTIFICACAO', 'CHAVE_INSCRITO', 'NUMFUNC', 'NUMVINC'}


class LinhaLoteSIGPEC(BaseModel):
    """Schema de validação de uma linha do arquivo TXT de lotes SIGPEC."""

    lote: int
    empresa: str
    vaga: str
    identificacao: int
    chave_inscrito: str = ''  # opcional — ignorado na integração
    numfunc: int
    numvinc: int | None = None  # opcional

    @field_validator('empresa', 'vaga', mode='before')
    @classmethod
    def nao_vazio(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError('Campo não pode estar vazio.')
        return str(v).strip()


def _validar_linha_lote(
    row: dict,
    num_linha: int,
    lote_referencia: int | None,
) -> tuple[LinhaLoteSIGPEC | None, list[dict], int | None]:
    """
    Valida uma linha do arquivo de lotes via schema Pydantic.

    Retorna (objeto_valido, erros, lote_referencia).
    Se houver erros de validação, objeto_valido é None e erros contém os detalhes.
    """
    identificacao = row.get('IDENTIFICACAO', '').strip()

    try:
        obj = LinhaLoteSIGPEC(
            lote=row.get('LOTE', '').strip(),
            empresa=row.get('EMPRESA', '').strip(),
            vaga=row.get('VAGA', '').strip(),
            identificacao=row.get('IDENTIFICACAO', '').strip(),
            chave_inscrito=row.get('CHAVE_INSCRITO', '').strip(),
            numfunc=row.get('NUMFUNC', '').strip(),
            numvinc=row.get('NUMVINC', '').strip() or None,
        )
    except ValidationError as exc:
        erros = [
            {
                'linha': num_linha,
                'identificacao': identificacao,
                'mensagem': f"Campo '{e['loc'][0]}': {e['msg']}",
            }
            for e in exc.errors()
        ]
        return None, erros, lote_referencia

    # Validação de unicidade do lote (cross-row — não pertence ao schema Pydantic)
    if lote_referencia is None:
        lote_referencia = obj.lote
    elif obj.lote != lote_referencia:
        return None, [{
            'linha': num_linha,
            'identificacao': identificacao,
            'mensagem': f"Lote '{obj.lote}' diverge do lote inicial '{lote_referencia}'.",
        }], lote_referencia

    return obj, [], lote_referencia


@captura_erros_importacao(param_nome_obj='importacao_obj')
def validar_txt_lotes(arquivo, importacao_obj=None) -> tuple[list[dict[str, Any]], list[dict]]:
    """
    Lê e valida o arquivo TXT de lotes.

    - Delimitador: ';'
    - Header fixo: LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC
    - Linhas vazias são ignoradas
    - Todos os registros devem possuir o mesmo valor na coluna LOTE
    - Todos os erros de linha são coletados antes de retornar (sem fail-fast)

    Retorna:
        (registros_validos, erros_por_linha)

    Lança exceções de domínio para erros estruturais (encoding, arquivo vazio, header inválido)
    que impedem o processamento linha a linha.
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
    erros_por_linha: list[dict] = []
    lote_referencia: int | None = None

    for row in reader:
        # Ignorar linhas completamente vazias
        valores = [v for k, v in row.items() if k and v is not None and str(v).strip()]
        if not valores:
            continue

        obj, erros_linha, lote_referencia = _validar_linha_lote(
            row, reader.line_num, lote_referencia
        )

        if erros_linha:
            erros_por_linha.extend(erros_linha)
        else:
            registros.append(obj.model_dump())

    if not registros and not erros_por_linha:
        raise ArquivoLotesVazioException(
            mensagem='O arquivo nao contem registros validos.',
            detalhes='Apenas cabecalho ou linhas vazias foram encontradas.',
        )

    logger.info(
        'validar_txt_lotes: %d registros validos, %d erros encontrados.',
        len(registros),
        len(erros_por_linha),
    )
    return registros, erros_por_linha

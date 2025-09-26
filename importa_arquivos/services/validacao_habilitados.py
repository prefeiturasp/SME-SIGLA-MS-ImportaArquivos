import csv
import io
import logging
from typing import List, Dict, Tuple

from importa_arquivos.models import LayoutArquivoImportacao
from importa_arquivos.services.exceptions import ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException
from .erros import captura_erros_importacao


logger = logging.getLogger(__name__)


@captura_erros_importacao(param_nome_obj='importacao_obj')
def validar_csv_habilitados(arquivo, importacao_obj=None) -> Tuple[List[Dict], List[Dict]]:
    """
    Valida o arquivo CSV enviado para HABILITADOS contra o layout configurado
    e retorna a lista de registros (linhas) como dicts, além da estrutura do layout.

    - Busca o layout mais recente com tipo 'HABILITADOS'
    - Compara cabeçalhos do CSV com as colunas definidas em estrutura[*].coluna
    - Cabeçalhos não previstos no layout são apenas logados como warning
    - Em caso de erro de leitura ou ausência de layout, levanta exceções customizadas
    """
    try:
        layout = LayoutArquivoImportacao.objects.filter(tipo='HABILITADOS').latest('criado_em')
    except LayoutArquivoImportacao.DoesNotExist:
        raise LayoutNaoConfiguradoException('Layout HABILITADOS não configurado.')

    estrutura: List[Dict] = layout.estrutura or []
    colunas_esperadas = {item.get('coluna') for item in estrutura if isinstance(item, dict)}

    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
    except Exception as exc:
        raise LeituraCSVException('Erro ao ler arquivo CSV', detalhes=str(exc))

    headers_csv = set(reader.fieldnames or [])
    if headers_csv != colunas_esperadas:
        logger.warning(f'Colunas inválidas no CSV: {headers_csv}')
        raise ColunaCSVInvalidaException(
            'Colunas inválidas no arquivo CSV',
            detalhes=f'Encontradas: {sorted(headers_csv)} | Esperadas: {sorted(colunas_esperadas)}'
        )

    registros: List[Dict] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        registros.append(row)

    return registros, estrutura

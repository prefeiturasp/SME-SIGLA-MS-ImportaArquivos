import csv
import io
import logging
from typing import List, Dict, Tuple

from ..models.layout import LayoutArquivoImportacao

logger = logging.getLogger(__name__)


def validar_csv_habilitados(arquivo) -> Tuple[List[Dict], List[Dict]]:
    """
    Valida o arquivo CSV enviado para HABILITADOS contra o layout configurado
    e retorna a lista de registros (linhas) como dicts, além da estrutura do layout.

    - Busca o layout mais recente com tipo 'HABILITADOS'
    - Compara cabeçalhos do CSV com as colunas definidas em estrutura[*].coluna
    - Cabeçalhos não previstos no layout são apenas logados como warning
    - Em caso de erro de leitura ou ausência de layout, levanta ValueError
    """
    try:
        layout = LayoutArquivoImportacao.objects.filter(tipo='HABILITADOS').latest('criado_em')
    except LayoutArquivoImportacao.DoesNotExist:
        raise ValueError('Layout HABILITADOS não configurado.')

    estrutura: List[Dict] = layout.estrutura or []
    colunas_esperadas = {item.get('coluna') for item in estrutura if isinstance(item, dict)}

    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
    except Exception as exc:
        raise ValueError(f'Erro ao ler CSV: {exc}')

    headers_csv = set(reader.fieldnames or [])
    for coluna in headers_csv:
        if coluna not in colunas_esperadas:
            logger.warning('Coluna não prevista no layout: %s', coluna)

    registros: List[Dict] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        registros.append(row)

    return registros, estrutura 
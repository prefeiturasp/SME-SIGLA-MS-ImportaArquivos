import csv
import io
import logging
from typing import List, Dict, Tuple

from ..models.layout import LayoutArquivoImportacao
from importa_arquivos.services.exceptions import ColunaCSVInvalidaException

logger = logging.getLogger(__name__)


def validar_csv_vagas(arquivo) -> Tuple[List[Dict], List[Dict]]:
    """
    Valida o arquivo CSV enviado para VAGAS contra o layout configurado
    e retorna a lista de registros (linhas) como dicts, além da estrutura do layout.
    """
    try:
        layout = LayoutArquivoImportacao.objects.filter(tipo='VAGAS').latest('criado_em')
    except LayoutArquivoImportacao.DoesNotExist:
        raise ValueError('Layout VAGAS não configurado.')

    estrutura: List[Dict] = layout.estrutura or []
    colunas_esperadas = {item.get('coluna') for item in estrutura if isinstance(item, dict)}
    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text), delimiter=';')
    except Exception as exc:
        raise ValueError(f'Erro ao ler CSV: {exc}')

    headers_csv = set(reader.fieldnames or [])
    if headers_csv != colunas_esperadas:
        logger.warning(f'Colunas inválidas no CSV: {headers_csv}')
        raise ColunaCSVInvalidaException(f'Colunas inválidas no CSV: {headers_csv}')

    registros: List[Dict] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        registros.append(row)

    return registros, estrutura 
import csv
import io
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from validate_docbr import CPF

from importa_arquivos.models import LayoutArquivoImportacao
from importa_arquivos.services.exceptions import ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException
from .erros import captura_erros_importacao


logger = logging.getLogger(__name__)


def _validar_obrigatoriedade_linhas(estrutura: List[Dict], registros: List[Dict]) -> Dict[int, List[str]]:
    """
    Valida campos obrigatórios linha a linha conforme a estrutura do layout.
    Retorna a lista de registros (dicts) quando não há erros; caso contrário lança exceção.
    """
    erros_por_linha: Dict[int, List[str]] = {}

    def _eh_obrigatorio(valor):
        try:
            return str(valor).strip() in ('1', 'true', 'True')
        except Exception:
            return False

    colunas_obrigatorias = [
        (item.get('coluna'), item)
        for item in estrutura if isinstance(item, dict) and _eh_obrigatorio(item.get('obrigatorio'))
        if item.get('coluna')
    ]

    for idx, row in enumerate(registros, start=2):  # Header na linha 1

        faltantes = []
        for coluna, _item in colunas_obrigatorias:
            valor = row.get(coluna)
            if valor is None or str(valor).strip() == '':
                faltantes.append(coluna)

        if faltantes:
            erros_por_linha.setdefault(idx, []).append(
                f"Campos obrigatórios vazios: {', '.join(sorted(faltantes))}"
            )
    return erros_por_linha


def _validar_formato_email(estrutura: List[Dict], registros: List[Dict]) -> Dict[int, List[str]]:
    """
    Valida o formato de e-mail conforme coluna definida no layout (campo_payload='email' ou coluna 'Email').
    Lança EmailFormatoInvalidoException com detalhe agregando linhas com e-mail inválido.
    """
    email_coluna = None
    for item in estrutura:
        if not isinstance(item, dict):
            continue
        campo = str(item.get('campo_payload', '')).lower()
        coluna = item.get('coluna')
        if campo == 'email' or (isinstance(coluna, str) and coluna.lower() in ('email', 'e-mail')):
            email_coluna = coluna
            break
    if not email_coluna:
        return {}

    import re
    regex = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    erros_por_linha: Dict[int, List[str]] = {}
    for idx, row in enumerate(registros, start=2):
        valor = row.get(email_coluna)
        if valor is None or str(valor).strip() == '':
            continue
        if not regex.match(str(valor).strip()):
            erros_por_linha.setdefault(idx, []).append(
                f"Email inválido -> '{valor}'"
            )
    return erros_por_linha


def _validar_cpf(estrutura: List[Dict], registros: List[Dict]) -> Dict[int, List[str]]:
    """
    Valida CPF usando validate_docbr.CPF(). Aceita valores com máscara; remove não dígitos.
    Coluna identificada por campo_payload='cpf' ou coluna 'CPF'.
    """
    cpf_coluna = None
    for item in estrutura:
        if not isinstance(item, dict):
            continue
        campo = str(item.get('campo_payload', '')).lower()
        coluna = item.get('coluna')
        # Valida CPF sempre que a coluna/campo esteja mapeada no layout
        if (campo == 'cpf' or (isinstance(coluna, str) and coluna.lower() == 'cpf')):
            cpf_coluna = coluna
            break
    if not cpf_coluna:
        return {}

    validator = CPF()
    erros_por_linha: Dict[int, List[str]] = {}
    for idx, row in enumerate(registros, start=2):
        valor = row.get(cpf_coluna)
        if valor is None or str(valor).strip() == '':
            continue
        digits = ''.join(ch for ch in str(valor) if ch.isdigit())
        if not validator.validate(digits):
            erros_por_linha.setdefault(idx, []).append(
                f"CPF inválido -> '{valor}'"
            )

    return erros_por_linha


def _validar_data_nascimento(estrutura: List[Dict], registros: List[Dict]) -> Dict[int, List[str]]:
    """
    Valida a coluna de data de nascimento no padrão mm/dd/yyyy.
    Coluna identificada por campo_payload='data_nascimento' ou nomes de coluna
    como 'DataNascimento'/'dataNascimento' (case-insensitive).
    """
    coluna_dn = None
    for item in estrutura:
        if not isinstance(item, dict):
            continue
        payload = str(item.get('campo_payload', '')).lower()
        coluna = item.get('coluna')
        if payload == 'data_nascimento' or (
            isinstance(coluna, str) and coluna.lower() in ('datanascimento', 'datanascimento')
        ):
            coluna_dn = coluna
            break
    if not coluna_dn:
        return {}

    erros_por_linha: Dict[int, List[str]] = {}
    for idx, row in enumerate(registros, start=2):
        valor = row.get(coluna_dn)
        if valor is None or str(valor).strip() == '':
            continue
        try:
            datetime.strptime(str(valor).strip(), '%m/%d/%Y')
        except Exception:
            erros_por_linha.setdefault(idx, []).append(
                f"dataNascimento inválida -> '{valor}' (esperado mm/dd/yyyy)"
            )

    return erros_por_linha


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
        raise LeituraCSVException('Erro ao ler arquivo de Habilitados', detalhes=f'Não foi possível ler o arquivo CSV. Detalhes: {str(exc)}')

    headers_csv = set(reader.fieldnames or [])
    if headers_csv != colunas_esperadas:
        logger.warning(f'Colunas inválidas no CSV: {headers_csv}')
        detalhes = f'Encontradas: {sorted(headers_csv)} | Esperadas: {sorted(colunas_esperadas)}'

        raise ColunaCSVInvalidaException('Arquivo de Habilitados inválido', detalhes=detalhes)

    registros: List[Dict] = []
    for row in reader:
        if isinstance(row, dict):
            registros.append(row)
    erros_obrig = _validar_obrigatoriedade_linhas(estrutura, registros)
    erros_email = _validar_formato_email(estrutura, registros)
    erros_cpf = _validar_cpf(estrutura, registros)
    erros_dn = _validar_data_nascimento(estrutura, registros)

    erros_agrupados: Dict[int, List[str]] = {}
    for src in (erros_obrig, erros_email, erros_cpf, erros_dn):
        for linha, msgs in src.items():
            erros_agrupados.setdefault(linha, []).extend(msgs)

    if erros_agrupados:
        mensagens = [f"Linha {linha}: {'; '.join(msgs)}" for linha, msgs in sorted(erros_agrupados.items())]
        detalhes = " | ".join(mensagens)
        logger.error("Erros de validação no CSV de Habilitados: %s", detalhes)
        raise ColunaCSVInvalidaException('Erros de validação encontrados', detalhes=detalhes)

    return registros, estrutura

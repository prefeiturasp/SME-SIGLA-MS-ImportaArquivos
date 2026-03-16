"""
Serviço de exportação de candidatos por processo.

Exige cargo_codigo (payload/registro). concurso_uuid e concurso_nome são opcionais.
concurso_codigo e concurso_data_criacao são opcionais (preenchidos no model quando informados).
Busca habilitados na API Candidatos, monta dados_concurso e lista_candidatos e formata o arquivo .txt (pipe, DD/MM/YYYY, CPF só dígitos).
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from .api_candidatos import ApiCandidatosService

_api_candidatos = ApiCandidatosService()

SEP = "|"
COLUNAS_LINHA = [
    "codigo", "data_criacao", "cd_cpf", "nm_candidato_concurso", "dt_nascimento", "cd_sexo",
    "nr_rg", "cd_cep", "nm_logradouro", "nr_logradouro", "tx_complemento", "nm_bairro",
    "nm_município", "sg_unidade_federativa", "nm_email", "nr_telefone_fixo", "nr_telefone_celular",
    "cd_cargo", "cd_vinculo", "cd_registro_funcional", "nr_classificação", "nr_desempate",
    "reservado", "nr_classificação_concurso",
]


def _buscar_habilitados(
    processo_uuid: str,
    codigo_cargo: int,
    concurso_uuid: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Obtém lista de habilitados via ApiCandidatosService."""
    return _api_candidatos.get_habilitados(
        processo_uuid, codigo_cargo, lote__concurso_uuid=concurso_uuid,
    )


def _data_para_dd_mm_yyyy(val: Any) -> str:
    """Converte data (ISO ou string) para DD/MM/YYYY."""
    if val is None or val == "":
        return ""
    s = str(val).strip()
    if not s:
        return ""
    if "T" in s:
        s = s.split("T")[0]
    if "-" in s:
        partes = s.split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
    if "/" in s and len(s) >= 8:
        return s
    return s


def _cpf_apenas_digitos(val: Any) -> str:
    """Retorna CPF apenas com dígitos."""
    return re.sub(r"\D", "", str(val)) if val is not None else ""


def _campo(val: Any) -> str:
    """Normaliza valor para o arquivo (sem pipe no conteúdo)."""
    if val is None:
        return ""
    s = str(val).strip().replace("\r", " ").replace("\n", " ")
    return s.replace(SEP, " ") if SEP in s else s


def formatar_arquivo_candidatos_processo(
    dados_concurso: Dict[str, Any],
    linhas_candidatos: List[Dict[str, Any]],
) -> str:
    """
    Gera o conteúdo do arquivo TXT (delimitado por |) sem cabeçalho.
    data_criacao e dt_nascimento em DD/MM/YYYY; cd_cpf apenas dígitos.
    """
    codigo_str = str(dados_concurso.get("codigo")) if dados_concurso.get("codigo") is not None else ""
    data_criacao = _data_para_dd_mm_yyyy(dados_concurso.get("data_criacao") or "")
    linhas: List[str] = []
    for item in linhas_candidatos:
        if not isinstance(item, dict):
            continue
        valores: List[str] = []
        for col in COLUNAS_LINHA:
            if col == "codigo":
                valores.append(_campo(codigo_str))
            elif col == "data_criacao":
                valores.append(data_criacao)
            elif col == "cd_cpf":
                valores.append(_cpf_apenas_digitos(item.get("cd_cpf")))
            elif col == "dt_nascimento":
                valores.append(_data_para_dd_mm_yyyy(item.get("dt_nascimento")))
            elif col == "reservado":
                valores.append("")
            else:
                valores.append(_campo(item.get(col)))
        linhas.append(SEP.join(valores))
    return "\n".join(linhas) + "\n" if linhas else ""


def _mapear_habilitado_para_exportacao(item: Dict[str, Any]) -> Dict[str, Any]:
    """Mapeia item da API de habilitados para a estrutura do arquivo (colunas esperadas pelo formatter)."""
    candidato = item.get('candidato') if isinstance(item.get('candidato'), dict) else {}
    dt_nasc = candidato.get('data_nascimento')
    dt_nasc = (str(dt_nasc).split('T')[0] if dt_nasc else '') if dt_nasc is not None else ''
    return {
        'cd_cpf': candidato.get('cpf') or '',
        'nm_candidato_concurso': candidato.get('nome') or '',
        'dt_nascimento': dt_nasc,
        'cd_sexo': candidato.get('genero') or '',
        'nr_rg': candidato.get('rg') or '',
        'cd_cep': candidato.get('cep') or '',
        'nm_logradouro': candidato.get('endereco') or '',
        'nr_logradouro': candidato.get('numero') or '',
        'tx_complemento': candidato.get('complemento') or '',
        'nm_bairro': candidato.get('bairro') or '',
        'nm_município': candidato.get('cidade') or '',
        'sg_unidade_federativa': candidato.get('estado') or '',
        'nm_email': candidato.get('email') or '',
        'nr_telefone_fixo': candidato.get('telefone') or '',
        'nr_telefone_celular': candidato.get('celular') or '',
        'cd_cargo': item.get('codigo_cargo') or '',
        'cd_vinculo': candidato.get('vinculo') or '',
        'cd_registro_funcional': candidato.get('registro_funcional') or '',
        'nr_classificação': item.get('ranking_escolha'),
        'nr_desempate': '',
        'nr_classificação_concurso': item.get('classificacao'),
    }

def exportar_candidatos_processo(
    processo_uuid: str,
    cargo_uuid: str,
    concurso_uuid: Optional[str] = None,
    processo_nome: Optional[str] = None,
    cargo_nome: Optional[str] = None,
    cargo_codigo: Optional[Any] = None,
    concurso_codigo: Optional[Any] = None,
    concurso_data_criacao: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Orquestra a exportação de candidatos por processo.
    Obtém habilitados; retorna (dados_concurso, lista_candidatos).
    """
    cargo_nome_final = (cargo_nome or "").strip()
    dados_concurso: Dict[str, Any] = {
        'codigo': None,
        'data_criacao': '',
        'cargo_codigo': cargo_codigo,
        'cargo_nome': cargo_nome_final,
        'processo_uuid': processo_uuid,
    }
    if concurso_uuid:
        if concurso_codigo is not None:
            dados_concurso['codigo'] = concurso_codigo
        if concurso_data_criacao is not None and (concurso_data_criacao or "").strip():
            dados_concurso['data_criacao'] = (concurso_data_criacao or "").strip()

    lista_bruta = _buscar_habilitados(processo_uuid, cargo_codigo, concurso_uuid=concurso_uuid)
    _chave = lambda i: (i.get('ranking_escolha') is None, i.get('ranking_escolha') or 0)
    lista_ordenada = sorted((i for i in lista_bruta if isinstance(i, dict)), key=_chave)
    lista_candidatos = [_mapear_habilitado_para_exportacao(item) for item in lista_ordenada]
    return (dados_concurso, lista_candidatos)

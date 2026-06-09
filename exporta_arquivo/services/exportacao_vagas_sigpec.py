"""Serviço de exportação de vagas por setor (escola) para formato SIGPEC.

Exige cargo_codigo no payload do create ou na query (download direto).
Busca vagas na API de escolha e monta a lista de linhas para o arquivo.
"""

from typing import Any

from exporta_arquivo.serializers.exportacao_vagas_sigpec import (
    VagasPayloadSerializer,
)

from .api_escolhas import ApiEscolhasService

SIGPEC_HEADER_LINES = [
    "@TABELA=[C_ERGON][PMSP_VAGAS_SME][1.0]",
    "@CHAVE=[SETOR][VARCHAR2]",
    "@TAG INICIO=",
    "@TAG FIM=",
    "@SEPARADOR=;",
    "@FORMATO DATA=DD/MM/YYYY",
    "@COLUNAS=[SETOR][VARCHAR2][VAGAS_DEFINITIVAS][NUMBER][VAGAS_PRECARIAS][NUMBER]",
]


def formatar_arquivo_sigpec(vagas_listas: list[dict[str, Any]]) -> str:
    """Recebe lista de dicts com chaves 'codigo_integracao', 'vagas_definitivas',.
    
    Args:
        vagas_listas: Parâmetro vagas listas da operação.
    
    Returns:
        Texto resultante da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    partes = list(SIGPEC_HEADER_LINES)
    for item in vagas_listas:
        codigo_integracao = str(item.get("codigo_integracao", "")).strip()
        v_def = item.get("vagas_definitivas", 0)
        v_prec = item.get("vagas_precarias", 0)

        partes.append(f"{codigo_integracao};{v_def};{v_prec};")
    return "\n".join(partes) + "\n"


def buscar_vagas_escolas(
    processo_uuid: str,
    cargo_codigo: int,
) -> list[dict[str, Any]]:
    """Chama ApiEscolhasService (vagas-escolas) com processo_uuid e cargo_codigo.
    
    Args:
        processo_uuid: Parâmetro processo uuid da operação.
        cargo_codigo: Parâmetro cargo codigo da operação.
    
    Returns:
        Lista com os registros resultantes.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    data = ApiEscolhasService().get_vagas_escolas(processo_uuid, cargo_codigo)
    serializer = VagasPayloadSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    vagas = serializer.validated_data["vagas"]

    vagas_listas = [
        {
            "codigo_integracao": v["escola"]["codigo_integracao"],
            "vagas_definitivas": v["vagas_definitivas"],
            "vagas_precarias": v["vagas_precarias"],
        }
        for v in vagas
        if v["escola"]["codigo_integracao"] is not None
        and v["escola"]["codigo_integracao"] != ""
    ]
    return vagas_listas

"""Serviço de exportação de vagas por processo (formato vagas processo).

Exige cargo_codigo no payload do create ou na query (download direto).
Busca vagas na API de escolha e monta a lista de linhas para o arquivo.
"""

from typing import Any

from exporta_arquivo.serializers.exportacao_vagas_sigpec import (
    VagasPayloadSerializer,
)

from .api_escolhas import ApiEscolhasService


def formatar_arquivo_vagas_processo(
    codigo_cargo: int,
    linhas: list[dict[str, Any]],
) -> str:
    """Recebe código do cargo (int) e lista de dicts com chaves 'setor'.

    Args:
        codigo_cargo: Codigo cargo utilizado na operação.
        linhas: Linhas utilizado na operação.

    Returns:
        Texto resultante da operação.
    """
    partes: list[str] = []
    for item in linhas:
        codigo_eol = str(item.get("codigo_eol", "")).strip()
        v_def = int(item.get("vagas_definitivas", 0) or 0)
        v_prec = int(item.get("vagas_precarias", 0) or 0)
        partes.append(f"{codigo_cargo}|{codigo_eol}|{v_def}|{v_prec}")
    return "\n".join(partes) + "\n" if partes else ""


def buscar_vagas_escolas(
    processo_uuid: str,
    cargo_codigo: int,
) -> list[dict[str, Any]]:
    """Busca vagas escolas.

    Args:
        processo_uuid: UUID do processo de convocação.
        cargo_codigo: Cargo codigo utilizado na operação.

    Returns:
        Lista com os registros obtidos.
    """
    data = ApiEscolhasService().get_vagas_escolas(processo_uuid, cargo_codigo)
    serializer = VagasPayloadSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    vagas = serializer.validated_data["vagas"]

    vagas_listas = [
        {
            "codigo_eol": v["escola"].get("codigo_eol"),
            "vagas_definitivas": v["vagas_definitivas"],
            "vagas_precarias": v["vagas_precarias"],
        }
        for v in vagas
    ]
    return vagas_listas

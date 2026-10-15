"""Blocos de documentação comuns aos recursos de exportação."""

from __future__ import annotations

from typing import Any

from core.openapi import (
    exemplos_requisicao,
    resposta,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import ErrosValidacaoSerializer
from django.db.models import Model
from drf_spectacular.utils import OpenApiParameter, extend_schema

UUID_CARGO_EXEMPLO = "9b2f6c1e-3a4d-4e8f-b7a1-6c5d4e3f2a10"
NOME_CARGO_EXEMPLO = "Professor de Educação Infantil"
CODIGO_CARGO_EXEMPLO = 3859

DESCRICAO_ARQUIVO = (
    "Arquivo de texto. O nome do arquivo vem no header "
    "`Content-Disposition`."
)


def operacoes_de_registro(
    *,
    recurso: str,
    identificador: str,
    modelo: type[Model],
    parametro: OpenApiParameter,
    serializer_detalhe: Any,
    serializer_edicao: Any,
    exemplo_detalhe: dict[str, Any],
    exemplo_edicao: dict[str, Any],
    exemplo_alteracao: dict[str, Any],
    exemplo_incompleto: dict[str, Any],
    exemplo_invalido: dict[str, Any],
) -> dict[str, Any]:
    """Monta detalhar, substituir, alterar e excluir de uma exportação.

    Substituir e alterar são rotas herdadas do CRUD genérico: mudam os
    dados do registro, sem gerar o arquivo de novo.

    Args:
        recurso: Nome do recurso no singular, com preposição (por exemplo
            ``de lote``).
        identificador: Sufixo dos ``operation_id``.
        modelo: Model do registro, usado na mensagem de 404.
        parametro: Parâmetro de rota que identifica o registro.
        serializer_detalhe: Modelo da resposta de detalhe.
        serializer_edicao: Modelo do corpo e da resposta de edição.
        exemplo_detalhe: Exemplo da resposta de detalhe.
        exemplo_edicao: Exemplo do corpo e da resposta de edição.
        exemplo_alteracao: Exemplo do corpo de alteração parcial.
        exemplo_incompleto: Erro de validação por campo obrigatório ausente.
        exemplo_invalido: Erro de validação por valor inválido.

    Returns:
        Mapa de ação para decorator, pronto para ``extend_schema_view``.
    """
    nao_encontrado = resposta_nao_encontrado(modelo)
    editado = resposta(
        serializer_edicao,
        "Dados editáveis do registro após a alteração.",
        {"Registro alterado": exemplo_edicao},
    )
    return {
        "retrieve": extend_schema(
            operation_id=f"detalhar_exportacao_{identificador}",
            summary=f"Detalhar exportação {recurso}",
            description=(
                f"Retorna o registro de uma exportação {recurso}. O "
                "conteúdo do arquivo não vem nesta resposta: use a rota de "
                "download."
            ),
            parameters=[parametro],
            responses=respostas(
                {
                    200: resposta(
                        serializer_detalhe,
                        "Registro da exportação.",
                        {"Exportação": exemplo_detalhe},
                    ),
                    404: nao_encontrado,
                }
            ),
        ),
        "update": extend_schema(
            operation_id=f"atualizar_exportacao_{identificador}",
            summary=f"Substituir os dados de uma exportação {recurso}",
            description=(
                "Rota herdada do CRUD genérico. Substitui os dados do "
                "registro, mas não gera o arquivo de novo: o download "
                "continua devolvendo o arquivo da geração original."
            ),
            parameters=[parametro],
            request=serializer_edicao,
            examples=exemplos_requisicao({"Dados": exemplo_edicao}),
            responses=respostas(
                {
                    200: editado,
                    400: resposta(
                        ErrosValidacaoSerializer,
                        "Dados inválidos.",
                        {"Campos obrigatórios ausentes": exemplo_incompleto},
                    ),
                    404: nao_encontrado,
                }
            ),
        ),
        "partial_update": extend_schema(
            operation_id=f"atualizar_parcial_exportacao_{identificador}",
            summary=f"Alterar os dados de uma exportação {recurso}",
            description=(
                "Rota herdada do CRUD genérico. Altera apenas os campos "
                "enviados, sem gerar o arquivo de novo."
            ),
            parameters=[parametro],
            request=serializer_edicao,
            examples=exemplos_requisicao(
                {"Corrigir um dado": exemplo_alteracao}
            ),
            responses=respostas(
                {
                    200: editado,
                    400: resposta(
                        ErrosValidacaoSerializer,
                        "Dados inválidos.",
                        {"Valor inválido": exemplo_invalido},
                    ),
                    404: nao_encontrado,
                }
            ),
        ),
        "destroy": extend_schema(
            operation_id=f"excluir_exportacao_{identificador}",
            summary=f"Excluir exportação {recurso}",
            description=(
                "Rota herdada do CRUD genérico. Exclui o registro da "
                "exportação, junto com o arquivo guardado nele."
            ),
            parameters=[parametro],
            responses=respostas(
                {
                    204: resposta(None, "Exportação excluída."),
                    404: nao_encontrado,
                }
            ),
        ),
    }

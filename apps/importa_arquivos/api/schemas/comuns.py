"""Blocos de documentação comuns aos recursos de importação."""

from __future__ import annotations

from typing import Any

from core.openapi import (
    TEXTO,
    exemplos_requisicao,
    resposta,
    resposta_arquivo,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import ErrosValidacaoSerializer
from django.db.models import Model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
)

from importa_arquivos.models.constants import (
    CHOICES_STATUS_IMPORTACAO_ARQUIVO,
)
from importa_arquivos.serializers import ErroImportacaoSerializer

MULTIPART = "multipart/form-data"
JSON = "application/json"

STATUS_IMPORTACAO = [codigo for codigo, _ in CHOICES_STATUS_IMPORTACAO_ARQUIVO]

EXEMPLO_ERRO_DA_IMPORTACAO = {
    "mensagem": "Erros de validação encontrados",
    "erros": (
        "Linha 2: CPF inválido -> '123' | Linha 3: Email inválido -> "
        "'maria-sem-arroba'"
    ),
    "criado_em": "2026-09-12T14:20:05-03:00",
}

EXEMPLO_ARQUIVO_DE_ERROS = (
    "**Linha 2:** CPF inválido -> '123'\n"
    "**Linha 3:** Email inválido -> 'maria-sem-arroba'"
)

ERRO_REQUISICAO_IMPORTACAO = PolymorphicProxySerializer(
    component_name="ErroRequisicaoImportacao",
    serializers=[ErrosValidacaoSerializer, ErroImportacaoSerializer],
    resource_type_field_name=None,
    many=False,
)

PARAMETRO_STATUS = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    enum=STATUS_IMPORTACAO,
    description="Retorna apenas as importações na situação informada.",
)

PARAMETRO_NOME_ARQUIVO = OpenApiParameter(
    name="nome_arquivo",
    type=OpenApiTypes.STR,
    description=(
        "Retorna apenas as importações cujo nome de arquivo é exatamente o "
        "informado."
    ),
)

PARAMETRO_IMPORTACAO_UUID = OpenApiParameter(
    name="importacao_uuid",
    type=OpenApiTypes.UUID,
    description=(
        "Retorna apenas os erros da importação com o UUID informado. Sem o "
        "parâmetro, vêm os erros de todas as importações deste tipo. Um "
        "valor que não seja UUID resulta em erro 500."
    ),
)

RESPOSTA_ERRO_INTERNO_DE_ERROS = resposta(
    None,
    (
        "Erro inesperado no servidor. Acontece também quando "
        "`importacao_uuid` não é um UUID. O corpo não segue um modelo JSON."
    ),
)


def operacao_baixar_erros(recurso: str, identificador: str) -> Any:
    """Monta a operação que devolve os erros de importação em texto.

    Args:
        recurso: Nome do recurso no plural, como aparece nos textos (por
            exemplo ``habilitados``).
        identificador: Sufixo do ``operation_id``.

    Returns:
        Decorator ``extend_schema`` da operação.
    """
    return extend_schema(
        operation_id=f"baixar_erros_importacao_{identificador}",
        summary=f"Baixar os erros das importações de {recurso}",
        description=(
            f"Devolve, em um arquivo de texto, os erros registrados nas "
            f"importações de {recurso}. Cada motivo ocupa uma linha e uma "
            "linha em branco separa um erro registrado do seguinte. O "
            "arquivo vem vazio quando não há erros."
        ),
        parameters=[PARAMETRO_IMPORTACAO_UUID],
        responses=respostas(
            {
                (200, TEXTO): resposta_arquivo(
                    "Arquivo de texto com os erros.",
                    {"Erros de validação": EXEMPLO_ARQUIVO_DE_ERROS},
                ),
                500: RESPOSTA_ERRO_INTERNO_DE_ERROS,
            }
        ),
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
    exemplo_substituicao: dict[str, Any],
    exemplo_alteracao: dict[str, Any],
) -> dict[str, Any]:
    """Monta detalhar, substituir, alterar e excluir de uma importação.

    Substituir e alterar são rotas herdadas do CRUD genérico: trocam o
    arquivo e os dados do registro, sem processar o arquivo de novo.

    Args:
        recurso: Nome do recurso no singular, com preposição (por exemplo
            ``de habilitados``).
        identificador: Sufixo dos ``operation_id``.
        modelo: Model do registro, usado na mensagem de 404.
        parametro: Parâmetro de rota que identifica o registro.
        serializer_detalhe: Modelo da resposta de detalhe.
        serializer_edicao: Modelo do corpo e da resposta de edição.
        exemplo_detalhe: Exemplo da resposta de detalhe.
        exemplo_edicao: Exemplo da resposta de edição.
        exemplo_substituicao: Exemplo do formulário de substituição.
        exemplo_alteracao: Exemplo do corpo de alteração parcial.

    Returns:
        Mapa de ação para decorator, pronto para ``extend_schema_view``.
    """
    nao_encontrado = resposta_nao_encontrado(modelo)
    editado = resposta(
        serializer_edicao,
        "Dados editáveis do registro após a alteração.",
        {"Registro alterado": exemplo_edicao},
    )
    invalido = resposta(
        ErrosValidacaoSerializer,
        "Dados inválidos.",
        {
            "UUID malformado": {
                "concurso_uuid": ["Must be a valid UUID."],
            }
        },
    )
    return {
        "retrieve": extend_schema(
            operation_id=f"detalhar_importacao_{identificador}",
            summary=f"Detalhar importação {recurso}",
            description=(
                f"Retorna uma importação {recurso} com os erros "
                "registrados nela."
            ),
            parameters=[parametro],
            responses=respostas(
                {
                    200: resposta(
                        serializer_detalhe,
                        "Importação com o resultado do processamento.",
                        {"Importação": exemplo_detalhe},
                    ),
                    404: nao_encontrado,
                }
            ),
        ),
        "update": extend_schema(
            operation_id=f"atualizar_importacao_{identificador}",
            summary=f"Substituir os dados de uma importação {recurso}",
            description=(
                "Rota herdada do CRUD genérico. Troca o arquivo e os dados "
                "informados no registro, mas não processa o arquivo de "
                "novo: nada é enviado aos outros serviços, e `nome_arquivo` "
                "e `status` continuam os da importação original. O arquivo "
                "é obrigatório, por isso o corpo é `multipart/form-data`."
            ),
            parameters=[parametro],
            request={MULTIPART: serializer_edicao},
            examples=exemplos_requisicao(
                {"Novo arquivo": exemplo_substituicao}, MULTIPART
            ),
            responses=respostas(
                {
                    200: editado,
                    400: resposta(
                        ErrosValidacaoSerializer,
                        "Dados inválidos.",
                        {
                            "Arquivo ausente": {
                                "arquivo": ["Nenhum arquivo foi submetido."]
                            }
                        },
                    ),
                    404: nao_encontrado,
                }
            ),
        ),
        "partial_update": extend_schema(
            operation_id=f"atualizar_parcial_importacao_{identificador}",
            summary=f"Alterar os dados de uma importação {recurso}",
            description=(
                "Rota herdada do CRUD genérico. Altera apenas os campos "
                "enviados, sem processar o arquivo de novo. Aceita JSON "
                "quando o arquivo não é trocado."
            ),
            parameters=[parametro],
            request={JSON: serializer_edicao, MULTIPART: serializer_edicao},
            examples=exemplos_requisicao(
                {"Corrigir os dados": exemplo_alteracao}, JSON
            ),
            responses=respostas(
                {200: editado, 400: invalido, 404: nao_encontrado}
            ),
        ),
        "destroy": extend_schema(
            operation_id=f"excluir_importacao_{identificador}",
            summary=f"Excluir importação {recurso}",
            description=(
                "Rota herdada do CRUD genérico. Exclui o registro da "
                "importação. Os dados já enviados aos outros serviços não "
                "são desfeitos."
            ),
            parameters=[parametro],
            responses=respostas(
                {
                    204: resposta(None, "Importação excluída."),
                    404: nao_encontrado,
                }
            ),
        ),
    }

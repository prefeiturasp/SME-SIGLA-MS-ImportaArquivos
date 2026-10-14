"""Documentação OpenAPI das operações de importação de escolhas."""

from __future__ import annotations

from core.openapi import (
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
    RESPOSTA_PAGINA_INEXISTENTE,
    TAMANHO_PAGINA_PADRAO,
    UUID_CONCURSO_EXEMPLO,
    UUID_PROCESSO_EXEMPLO,
    exemplos_requisicao,
    parametro_busca,
    parametro_ordenacao,
    parametro_uuid,
    resposta,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from importa_arquivos.api.schemas.comuns import (
    ERRO_REQUISICAO_IMPORTACAO,
    PARAMETRO_IMPORTACAO_UUID,
    PARAMETRO_STATUS,
    RESPOSTA_ERRO_INTERNO_DE_ERROS,
    operacao_baixar_erros,
)
from importa_arquivos.models import ImportacaoEscolhas
from importa_arquivos.models.constants import CHOICES_MODO_IMPORTACAO_ESCOLHAS
from importa_arquivos.serializers import (
    ImportacaoErrosListSerializer,
    ImportacaoEscolhasCreateSerializer,
    ImportacaoEscolhasListSerializer,
    ImportacaoEscolhasPaginadoSerializer,
)

TAG_IMPORTACAO_ESCOLHAS = "Importação de escolhas"

MODOS = [codigo for codigo, _ in CHOICES_MODO_IMPORTACAO_ESCOLHAS]

EXEMPLO_REQUISICAO = {
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "processo_id": 820,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
}

EXEMPLO_IMPORTACAO = {
    "uuid": "4c3b2a19-0f8e-4d7c-9b6a-5e4d3c2b1a09",
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "processo_id": 820,
    "dados_prodam": [
        {
            "codigoPessoaFisica": "52998224725",
            "codigoCargo": "3859",
            "codigoUnidadeAlocacao": "094765",
            "tipoVaga": "D",
            "descricaoStatus": "ALOCADO",
        }
    ],
    "status": "CONCLUIDO",
    "modo": "MANUAL",
    "criado_em": "2026-09-16T08:00:00-03:00",
    "atualizado_em": "2026-09-16T08:00:04-03:00",
    "erros": None,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "processo_nome": None,
}

EXEMPLO_PAGINA = {
    "links": {"next": None, "previous": None},
    "count": 1,
    "page": 1,
    "page_size": TAMANHO_PAGINA_PADRAO,
    "results": [EXEMPLO_IMPORTACAO],
}

EXEMPLO_ERRO_LISTADO = {
    "mensagem": "Erro na resposta da API PRODAM",
    "erros": "Processo 819 não localizado.",
    "concurso_uuid": None,
    "processo_uuid": None,
}

PARAMETRO_UUID = parametro_uuid("UUID da importação de escolhas.")

PARAMETROS_LISTAGEM = [
    OpenApiParameter(
        name="processo_uuid",
        type=OpenApiTypes.UUID,
        description=(
            "Retorna apenas as importações do processo de convocação "
            "informado."
        ),
    ),
    PARAMETRO_STATUS,
    OpenApiParameter(
        name="processo_id",
        type=OpenApiTypes.INT,
        description=(
            "Retorna apenas as importações feitas com o identificador de "
            "processo da PRODAM informado."
        ),
    ),
    OpenApiParameter(
        name="modo",
        type=OpenApiTypes.STR,
        enum=MODOS,
        description=(
            "Retorna apenas as importações disparadas do modo informado."
        ),
    ),
    parametro_busca("Busca por trecho do UUID do processo."),
    parametro_ordenacao(["status", "criado_em"], "-criado_em"),
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
]

RESPOSTA_NAO_ENCONTRADO = resposta_nao_encontrado(ImportacaoEscolhas)

RESPOSTA_SEM_IMPLEMENTACAO = resposta(
    None,
    (
        "Resposta para qualquer corpo válido: a rota não está implementada "
        "e termina em erro inesperado. O corpo não segue um modelo JSON."
    ),
)

RESPOSTA_CORPO_INVALIDO = resposta(
    ErrosValidacaoSerializer,
    "Dados inválidos.",
    {
        "UUID malformado": {
            "processo_uuid": ["Must be a valid UUID."],
        }
    },
)

OPERACOES_IMPORTACAO_ESCOLHAS = {
    "list": extend_schema(
        operation_id="listar_importacoes_escolhas",
        summary="Listar importações de escolhas",
        description=(
            "Lista as importações de escolhas, da mais recente para a mais "
            "antiga, com paginação. Entram as disparadas por esta API e as "
            "da rotina agendada, inclusive as que terminaram em erro."
        ),
        parameters=PARAMETROS_LISTAGEM,
        responses=respostas(
            {
                200: resposta(
                    ImportacaoEscolhasPaginadoSerializer,
                    "Página de importações de escolhas.",
                    {"Lista paginada": EXEMPLO_PAGINA},
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    (
                        "Filtro `processo_uuid`, `status`, `processo_id` ou "
                        "`modo` com valor inválido."
                    ),
                    {
                        "Modo inexistente": {
                            "modo": [
                                "Faça uma escolha válida. X não é uma das "
                                "escolhas disponíveis."
                            ]
                        }
                    },
                ),
                404: RESPOSTA_PAGINA_INEXISTENTE,
            }
        ),
    ),
    "create": extend_schema(
        operation_id="importar_escolhas",
        summary="Importar escolhas da PRODAM",
        description=(
            "Busca na PRODAM o resultado de convocação do processo "
            "(`processo_id`) e envia as escolhas ao MS-Escolhas. A chamada "
            "só responde depois que as duas etapas terminam.\n\n"
            "Toda tentativa grava um registro de importação com `modo` "
            "`MANUAL`. Quando a PRODAM não devolve registros, a importação "
            "termina `CONCLUIDO` sem enviar nada.\n\n"
            "Falhas:\n\n"
            "- A PRODAM responde que não pôde atender: 400 com `detail`.\n"
            "- O MS-Escolhas recusa os dados: a resposta repete o código "
            "HTTP devolvido por ele (400, 404, 503…), com `detail` e "
            "`detalhes`.\n"
            "- A PRODAM ou o MS-Escolhas não respondem, ou a PRODAM devolve "
            "algo fora do formato: 500 com `detail`."
        ),
        request=ImportacaoEscolhasCreateSerializer,
        examples=exemplos_requisicao(
            {
                "Com o identificador da PRODAM": EXEMPLO_REQUISICAO,
                "Só os UUIDs": {
                    "processo_uuid": UUID_PROCESSO_EXEMPLO,
                    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
                },
            }
        ),
        responses=respostas(
            {
                201: resposta(
                    ImportacaoEscolhasListSerializer,
                    "Escolhas buscadas na PRODAM e enviadas ao MS-Escolhas.",
                    {"Importação concluída": EXEMPLO_IMPORTACAO},
                ),
                400: resposta(
                    ERRO_REQUISICAO_IMPORTACAO,
                    (
                        "Dados inválidos, recusa da PRODAM ou recusa do "
                        "MS-Escolhas. Na recusa do MS-Escolhas o código "
                        "pode ser outro, igual ao que ele devolveu."
                    ),
                    {
                        "Dados inválidos": {
                            "processo_uuid": ["Este campo é obrigatório."],
                            "concurso_uuid": ["Este campo é obrigatório."],
                        },
                        "PRODAM não atendeu": {
                            "detail": (
                                "Erro na API PRODAM: Processo 819 não "
                                "localizado."
                            )
                        },
                        "MS-Escolhas recusou os dados": {
                            "detail": (
                                "Falha ao enviar escolhas para API externa"
                            ),
                            "detalhes": "Status 400",
                        },
                    },
                ),
                500: resposta(
                    ErroDetalheSerializer,
                    (
                        "Falha de comunicação com a PRODAM ou com o "
                        "MS-Escolhas, ou resposta da PRODAM fora do formato."
                    ),
                    {
                        "PRODAM indisponível": {
                            "detail": (
                                "Erro ao processar importação: Erro ao "
                                "consultar API externa: 503 Server Error: "
                                "Service Unavailable for url: <URL da "
                                "PRODAM>"
                            )
                        }
                    },
                ),
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_importacao_escolhas",
        summary="Detalhar importação de escolhas",
        description=(
            "Retorna uma importação de escolhas com os dados devolvidos "
            "pela PRODAM e os erros registrados nela."
        ),
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {
                200: resposta(
                    ImportacaoEscolhasListSerializer,
                    "Importação com o resultado do processamento.",
                    {"Importação": EXEMPLO_IMPORTACAO},
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_importacao_escolhas",
        summary="Substituir os dados de uma importação de escolhas",
        description=(
            "Rota herdada do CRUD genérico que não está implementada. Com "
            "corpo inválido responde 400; com corpo válido, 500. Nenhum "
            "dado é alterado."
        ),
        parameters=[PARAMETRO_UUID],
        request=ImportacaoEscolhasCreateSerializer,
        examples=exemplos_requisicao({"Corpo válido": EXEMPLO_REQUISICAO}),
        responses=respostas(
            {
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Dados inválidos.",
                    {
                        "Campos obrigatórios ausentes": {
                            "processo_uuid": ["Este campo é obrigatório."],
                            "concurso_uuid": ["Este campo é obrigatório."],
                        }
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
                500: RESPOSTA_SEM_IMPLEMENTACAO,
            }
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_importacao_escolhas",
        summary="Alterar os dados de uma importação de escolhas",
        description=(
            "Rota herdada do CRUD genérico que não está implementada. Com "
            "corpo inválido responde 400; com corpo válido, inclusive "
            "vazio, 500. Nenhum dado é alterado."
        ),
        parameters=[PARAMETRO_UUID],
        request=ImportacaoEscolhasCreateSerializer,
        examples=exemplos_requisicao({"Corpo válido": {"processo_id": 820}}),
        responses=respostas(
            {
                400: RESPOSTA_CORPO_INVALIDO,
                404: RESPOSTA_NAO_ENCONTRADO,
                500: RESPOSTA_SEM_IMPLEMENTACAO,
            }
        ),
    ),
    "destroy": extend_schema(
        operation_id="excluir_importacao_escolhas",
        summary="Excluir importação de escolhas",
        description=(
            "Rota herdada do CRUD genérico. Exclui o registro da "
            "importação. As escolhas já enviadas ao MS-Escolhas não são "
            "desfeitas."
        ),
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {
                204: resposta(None, "Importação excluída."),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "listar_erros": extend_schema(
        operation_id="listar_erros_importacao_escolhas",
        summary="Listar os erros das importações de escolhas",
        description=(
            "Retorna os erros registrados nas importações de escolhas, do "
            "mais recente para o mais antigo, sem paginação."
        ),
        parameters=[PARAMETRO_IMPORTACAO_UUID],
        responses=respostas(
            {
                200: resposta(
                    ImportacaoErrosListSerializer(many=True),
                    "Erros registrados.",
                    {"Erro da PRODAM": EXEMPLO_ERRO_LISTADO},
                ),
                500: RESPOSTA_ERRO_INTERNO_DE_ERROS,
            }
        ),
    ),
    "download_erros": operacao_baixar_erros("escolhas", "escolhas"),
}

"""Documentação OpenAPI das operações do cabeçalho de exportação de lote."""

from __future__ import annotations

from core.openapi import (
    PARAMETRO_PAGINA_PADRAO,
    RESPOSTA_PAGINA_INEXISTENTE,
    exemplos_requisicao,
    parametro_uuid,
    resposta,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import ErrosValidacaoSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from exporta_arquivo.models import CabecalhoExportacaoLote
from exporta_arquivo.serializers import (
    CabecalhoExportacaoLotePaginadoSerializer,
    CabecalhoExportacaoLoteSerializer,
)

TAG_CABECALHO_EXPORTACAO_LOTE = "Cabeçalho da exportação de lotes"

AVISO_SEM_EFEITO = (
    "Hoje a exportação de lotes grava um cabeçalho fixo e não consulta este "
    "cadastro."
)

EXEMPLO_DADOS = {
    "tabela": "[c_ERGON][PMSP_ESCOLHA_VAGA_SME][1.0]",
    "chave": "[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER]",
    "tag_inicio": "",
    "tag_fim": "",
    "separador": ";",
    "formato_data": "DD/MM/YYYY",
    "colunas": (
        "[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER]"
        "[DATA_ESCOLHA][DATE][ESCOLHEU_VAGA][VARCHAR2][SETOR][VARCHAR2]"
    ),
    "ativo": True,
}

EXEMPLO_CABECALHO = {
    "uuid": "7a6b5c4d-3e2f-4a1b-8c0d-9e8f7a6b5c4d",
    "criado_em": "2026-03-02T10:00:00-03:00",
    "atualizado_em": "2026-03-02T10:00:00-03:00",
    **EXEMPLO_DADOS,
}

EXEMPLO_PAGINA = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [EXEMPLO_CABECALHO],
}

ERRO_SEPARADOR_LONGO = {
    "separador": [
        "Certifique-se de que este campo não tenha mais de 10 caracteres."
    ]
}

PARAMETRO_UUID = parametro_uuid("UUID do cabeçalho.")

RESPOSTA_CABECALHO = resposta(
    CabecalhoExportacaoLoteSerializer,
    "Cabeçalho.",
    {"Cabeçalho padrão": EXEMPLO_CABECALHO},
)

RESPOSTA_NAO_ENCONTRADO = resposta_nao_encontrado(CabecalhoExportacaoLote)

RESPOSTA_DADOS_INVALIDOS = resposta(
    ErrosValidacaoSerializer,
    "Dados inválidos.",
    {"Separador longo demais": ERRO_SEPARADOR_LONGO},
)

OPERACOES_CABECALHO_EXPORTACAO_LOTE = {
    "list": extend_schema(
        operation_id="listar_cabecalhos_exportacao_lote",
        summary="Listar cabeçalhos de exportação de lote",
        description=(
            "Lista os cabeçalhos cadastrados, do mais recente para o mais "
            f"antigo, com paginação. {AVISO_SEM_EFEITO}"
        ),
        parameters=[
            OpenApiParameter(
                name="ativo",
                type=OpenApiTypes.BOOL,
                description=(
                    "Retorna apenas os cabeçalhos ativos (`true`) ou "
                    "inativos (`false`). Outros valores são ignorados."
                ),
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                description=(
                    "Campo de ordenação: qualquer campo do cabeçalho, como "
                    "`criado_em` ou `ativo`. Prefixe com `-` para ordem "
                    "decrescente. Padrão: `-criado_em`."
                ),
            ),
            PARAMETRO_PAGINA_PADRAO,
        ],
        responses=respostas(
            {
                200: resposta(
                    CabecalhoExportacaoLotePaginadoSerializer,
                    "Página de cabeçalhos.",
                    {"Lista paginada": EXEMPLO_PAGINA},
                ),
                404: RESPOSTA_PAGINA_INEXISTENTE,
            }
        ),
    ),
    "create": extend_schema(
        operation_id="criar_cabecalho_exportacao_lote",
        summary="Criar cabeçalho de exportação de lote",
        description=(
            "Cadastra um cabeçalho. Todos os campos têm valor padrão, então "
            "o corpo pode ser `{}`. O serviço não desativa os cabeçalhos "
            f"anteriores: pode haver mais de um ativo. {AVISO_SEM_EFEITO}"
        ),
        request=CabecalhoExportacaoLoteSerializer,
        examples=exemplos_requisicao({"Cabeçalho padrão": EXEMPLO_DADOS}),
        responses=respostas(
            {
                201: resposta(
                    CabecalhoExportacaoLoteSerializer,
                    "Cabeçalho criado.",
                    {"Cabeçalho padrão": EXEMPLO_CABECALHO},
                ),
                400: RESPOSTA_DADOS_INVALIDOS,
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_cabecalho_exportacao_lote",
        summary="Detalhar cabeçalho de exportação de lote",
        description="Retorna um cabeçalho pelo UUID.",
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {200: RESPOSTA_CABECALHO, 404: RESPOSTA_NAO_ENCONTRADO}
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_cabecalho_exportacao_lote",
        summary="Atualizar cabeçalho de exportação de lote",
        description=(
            "Substitui os dados do cabeçalho. Campos não enviados mantêm o "
            "valor atual."
        ),
        parameters=[PARAMETRO_UUID],
        request=CabecalhoExportacaoLoteSerializer,
        examples=exemplos_requisicao({"Dados do cabeçalho": EXEMPLO_DADOS}),
        responses=respostas(
            {
                200: RESPOSTA_CABECALHO,
                400: RESPOSTA_DADOS_INVALIDOS,
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_cabecalho_exportacao_lote",
        summary="Atualizar cabeçalho de exportação de lote parcialmente",
        description="Altera apenas os campos enviados.",
        parameters=[PARAMETRO_UUID],
        request=CabecalhoExportacaoLoteSerializer,
        examples=exemplos_requisicao({"Desativar": {"ativo": False}}),
        responses=respostas(
            {
                200: RESPOSTA_CABECALHO,
                400: RESPOSTA_DADOS_INVALIDOS,
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "destroy": extend_schema(
        operation_id="excluir_cabecalho_exportacao_lote",
        summary="Excluir cabeçalho de exportação de lote",
        description="Exclui o cabeçalho.",
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {
                204: resposta(None, "Cabeçalho excluído."),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
}

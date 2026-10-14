"""Documentação OpenAPI das operações de exportação de lotes."""

from __future__ import annotations

from core.openapi import (
    NOME_CONCURSO_EXEMPLO,
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
    RESPOSTA_PAGINA_INEXISTENTE,
    TAMANHO_PAGINA_PADRAO,
    TEXTO,
    UUID_CONCURSO_EXEMPLO,
    exemplos_requisicao,
    parametro_busca,
    parametro_ordenacao,
    parametro_uuid,
    resposta,
    resposta_arquivo,
    respostas,
)
from core.serializers import (
    ErroDetalheSerializer,
    ErroProcessamentoSerializer,
    ErrosValidacaoSerializer,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
)

from exporta_arquivo.api.schemas.comuns import (
    DESCRICAO_ARQUIVO,
    operacoes_de_registro,
)
from exporta_arquivo.models import ExportacaoLote
from exporta_arquivo.serializers import (
    ExportacaoLoteCreateSerializer,
    ExportacaoLoteListSerializer,
    ExportacaoLotePaginadoSerializer,
)

TAG_EXPORTACAO_LOTE = "Exportação de lotes"

UUID_LOTE_EXEMPLO = "2f1e0d9c-8b7a-4f6e-9d5c-4b3a2f1e0d9c"

EXEMPLO_DADOS = {
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
    "numero_lote": 7,
    "lote_uuid": UUID_LOTE_EXEMPLO,
}

EXEMPLO_REGISTRO = {
    "uuid": "8c7b6a59-4e3d-4c2b-9a1f-0e9d8c7b6a59",
    "criado_em": "2026-09-22T16:05:00-03:00",
    "atualizado_em": "2026-09-22T16:05:02-03:00",
    **EXEMPLO_DADOS,
    "nome_arquivo": "exportacao_lote_7.txt",
    "status": "SUCESSO",
}

EXEMPLO_PAGINA = {
    "links": {"next": None, "previous": None},
    "count": 1,
    "page": 1,
    "page_size": TAMANHO_PAGINA_PADRAO,
    "results": [EXEMPLO_REGISTRO],
}

ARQUIVO_LOTE = (
    "@TABELA=[c_ERGON][PMSP_ESCOLHA_VAGA_SME][1.0]\n"
    "        @CHAVE=[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO]"
    "[NUMBER]\n"
    "        @TAG INICIO=\n"
    "        @TAG FIM=\n"
    "        @SEPARADOR=;\n"
    "        @FORMATO DATA=DD/MM/YYYY\n"
    "        @COLUNAS=[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO]"
    "[NUMBER][DATA_ESCOLHA][DATE][ESCOLHEU_VAGA][VARCHAR2][SETOR]"
    "[VARCHAR2]\n"
    "7;1;20250001;15092026;S;0094765;\n"
    "7;1;20250002;15092026;N;;\n"
)

ARQUIVO_SEM_ESCOLHA = (
    "Candidatos sem escolha realizada no lote 7:\n"
    "- Maria Aparecida da Silva\n"
)

ERRO_CAMPOS_OBRIGATORIOS = {
    "concurso_uuid": ["Este campo é obrigatório."],
    "concurso_nome": ["Este campo é obrigatório."],
    "numero_lote": ["Este campo é obrigatório."],
    "lote_uuid": ["Este campo é obrigatório."],
}

ERRO_CRIACAO = PolymorphicProxySerializer(
    component_name="ErroExportacaoLote",
    serializers=[ErrosValidacaoSerializer, ErroProcessamentoSerializer],
    resource_type_field_name=None,
    many=False,
)

PARAMETRO_UUID = parametro_uuid("UUID da exportação de lote.")

PARAMETROS_LISTAGEM = [
    OpenApiParameter(
        name="concurso_uuid",
        type=OpenApiTypes.UUID,
        description="Retorna apenas as exportações do concurso informado.",
    ),
    OpenApiParameter(
        name="lote_uuid",
        type=OpenApiTypes.UUID,
        description="Retorna apenas as exportações do lote informado.",
    ),
    OpenApiParameter(
        name="concurso_nome",
        type=OpenApiTypes.STR,
        description=(
            "Retorna apenas as exportações cujo nome de concurso é "
            "exatamente o informado."
        ),
    ),
    OpenApiParameter(
        name="numero_lote",
        type=OpenApiTypes.INT,
        description=(
            "Retorna apenas as exportações do lote com o número informado."
        ),
    ),
    OpenApiParameter(
        name="codigo_cargo",
        type=OpenApiTypes.STR,
        description=(
            "Retorna apenas as exportações gravadas com o código de cargo "
            "informado. Esta API não preenche esse dado ao exportar."
        ),
    ),
    parametro_busca("Busca por trecho do nome do concurso."),
    parametro_ordenacao(["criado_em", "atualizado_em"], "-criado_em"),
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
]

RESPOSTA_ARQUIVO = resposta_arquivo(
    DESCRICAO_ARQUIVO,
    {
        "Lote exportado": ARQUIVO_LOTE,
        "Candidatos sem escolha": ARQUIVO_SEM_ESCOLHA,
    },
)

OPERACOES_EXPORTACAO_LOTE = {
    "list": extend_schema(
        operation_id="listar_exportacoes_lote",
        summary="Listar exportações de lote",
        description=(
            "Lista os registros de exportação de lote, do mais recente "
            "para o mais antigo, com paginação. Entram também as "
            "tentativas com `status` `ATENCAO` e `ERRO`."
        ),
        parameters=PARAMETROS_LISTAGEM,
        responses=respostas(
            {
                200: resposta(
                    ExportacaoLotePaginadoSerializer,
                    "Página de registros de exportação de lote.",
                    {"Lista paginada": EXEMPLO_PAGINA},
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Filtro com valor inválido.",
                    {
                        "Número de lote não numérico": {
                            "numero_lote": ["Informe um número."]
                        }
                    },
                ),
                404: RESPOSTA_PAGINA_INEXISTENTE,
            }
        ),
    ),
    "create": extend_schema(
        operation_id="exportar_lote",
        summary="Gerar exportação de lote",
        description=(
            "Busca no MS-Candidatos os candidatos do lote (`concurso_uuid` "
            "e `numero_lote`) e, no MS-Escolhas, a escolha de cada um, e "
            "gera o arquivo do lote para o SIGPEC. Toda chamada com dados "
            "válidos grava um registro de exportação.\n\n"
            "- Todos os candidatos têm escolha: 200 com o arquivo, e o "
            "registro fica `SUCESSO`. O arquivo traz um cabeçalho fixo e "
            "uma linha por candidato, com lote, código SIGPEC, chave de "
            "inscrição, data da escolha (`ddmmaaaa`), situação e código de "
            "integração da unidade escolhida, separados por `;`. A "
            "situação é `S` para escolha, `N` para não escolha e `R` para "
            "reconvocação.\n"
            "- Algum candidato sem escolha: 422 com um arquivo de texto "
            "que lista os nomes pendentes, e o registro fica `ATENCAO`. É "
            "esse arquivo que o download devolve depois.\n"
            "- Falha ao consultar os outros serviços: 400 com `mensagem` e "
            "`detail`, e o registro fica `ERRO`.\n\n"
            "Um lote sem candidatos gera um arquivo só com o cabeçalho. "
            "`lote_uuid` é obrigatório, mas a busca dos candidatos usa "
            "`numero_lote`."
        ),
        request=ExportacaoLoteCreateSerializer,
        examples=exemplos_requisicao({"Lote 7": EXEMPLO_DADOS}),
        responses=respostas(
            {
                (200, TEXTO): resposta_arquivo(
                    DESCRICAO_ARQUIVO, {"Lote exportado": ARQUIVO_LOTE}
                ),
                400: resposta(
                    ERRO_CRIACAO,
                    (
                        "Dados inválidos ou falha ao consultar o "
                        "MS-Candidatos ou o MS-Escolhas."
                    ),
                    {
                        "Campos obrigatórios ausentes": (
                            ERRO_CAMPOS_OBRIGATORIOS
                        ),
                        "MS-Candidatos indisponível": {
                            "mensagem": (
                                "Serviço de candidatos (habilitados) "
                                "indisponível."
                            ),
                            "detail": "Status 503",
                        },
                    },
                ),
                (422, TEXTO): resposta_arquivo(
                    (
                        "Há candidatos do lote sem escolha. O corpo é um "
                        "arquivo de texto com os nomes pendentes."
                    ),
                    {"Candidatos sem escolha": ARQUIVO_SEM_ESCOLHA},
                ),
            }
        ),
    ),
    **operacoes_de_registro(
        recurso="de lote",
        identificador="lote",
        modelo=ExportacaoLote,
        parametro=PARAMETRO_UUID,
        serializer_detalhe=ExportacaoLoteListSerializer,
        serializer_edicao=ExportacaoLoteCreateSerializer,
        exemplo_detalhe=EXEMPLO_REGISTRO,
        exemplo_edicao=EXEMPLO_DADOS,
        exemplo_alteracao={"numero_lote": 8},
        exemplo_incompleto=ERRO_CAMPOS_OBRIGATORIOS,
        exemplo_invalido={
            "numero_lote": ["Um número inteiro válido é exigido."]
        },
    ),
    "download": extend_schema(
        operation_id="baixar_exportacao_lote",
        summary="Baixar o arquivo de uma exportação de lote",
        description=(
            "Devolve o arquivo guardado no registro: o arquivo do lote, "
            "quando a exportação terminou em `SUCESSO`, ou a lista de "
            "candidatos sem escolha, quando terminou em `ATENCAO`. "
            "Registros em `ERRO` não têm arquivo e respondem 404."
        ),
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {
                (200, TEXTO): RESPOSTA_ARQUIVO,
                404: resposta(
                    ErroDetalheSerializer,
                    "Registro não encontrado ou sem arquivo.",
                    {
                        "Identificador inexistente": {
                            "detail": (
                                "No ExportacaoLote matches the given query."
                            )
                        },
                        "Identificador malformado": {
                            "detail": "Não encontrado."
                        },
                        "Registro sem arquivo": {
                            "detail": (
                                "Arquivo não disponível para este registro."
                            )
                        },
                    },
                ),
            }
        ),
    ),
}

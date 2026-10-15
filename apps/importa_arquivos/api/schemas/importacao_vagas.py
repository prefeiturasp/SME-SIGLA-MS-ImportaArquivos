"""Documentação OpenAPI das operações de importação de vagas."""

from __future__ import annotations

from core.openapi import (
    NOME_PROCESSO_EXEMPLO,
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
    RESPOSTA_PAGINA_INEXISTENTE,
    TAMANHO_PAGINA_PADRAO,
    UUID_CONCURSO_EXEMPLO,
    UUID_PROCESSO_EXEMPLO,
    exemplos_requisicao,
    parametro_busca,
    parametro_id,
    parametro_ordenacao,
    resposta,
    respostas,
)
from core.serializers import ErrosValidacaoSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from importa_arquivos.api.schemas.comuns import (
    ERRO_REQUISICAO_IMPORTACAO,
    MULTIPART,
    PARAMETRO_NOME_ARQUIVO,
    PARAMETRO_STATUS,
    operacao_baixar_erros,
    operacoes_de_registro,
)
from importa_arquivos.api.schemas.layout import CABECALHO_VAGAS
from importa_arquivos.models import ImportacaoArquivoVagas
from importa_arquivos.serializers import (
    ImportacaoArquivoVagasCreateSerializer,
    ImportacaoArquivoVagasListSerializer,
    ImportacaoArquivoVagasPaginadoSerializer,
)

TAG_IMPORTACAO_VAGAS = "Importação de vagas"

EXEMPLO_FORMULARIO = {
    "arquivo": "vagas.csv",
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "processo_nome": NOME_PROCESSO_EXEMPLO,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
}

EXEMPLO_EDICAO = {
    "arquivo": "http://localhost:8000/media/importacoes/vagas.csv",
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "processo_nome": NOME_PROCESSO_EXEMPLO,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
}

EXEMPLO_IMPORTACAO = {
    "uuid": "0a9b8c7d-6e5f-4a3b-8c2d-1e0f9a8b7c6d",
    "nome_arquivo": "vagas.csv",
    "arquivo": "http://localhost:8000/media/importacoes/vagas.csv",
    "status": "PENDENTE",
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "processo_nome": NOME_PROCESSO_EXEMPLO,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "criado_em": "2026-09-10T09:15:00-03:00",
    "atualizado_em": "2026-09-10T09:15:00-03:00",
    "erros": None,
}

EXEMPLO_PAGINA = {
    "links": {"next": None, "previous": None},
    "count": 1,
    "page": 1,
    "page_size": TAMANHO_PAGINA_PADRAO,
    "results": [EXEMPLO_IMPORTACAO],
}

PARAMETRO_ID = parametro_id("da importação")

PARAMETROS_LISTAGEM = [
    PARAMETRO_NOME_ARQUIVO,
    PARAMETRO_STATUS,
    OpenApiParameter(
        name="processo_uuid",
        type=OpenApiTypes.UUID,
        description=(
            "Retorna apenas as importações do processo de convocação "
            "informado."
        ),
    ),
    OpenApiParameter(
        name="processo_nome",
        type=OpenApiTypes.STR,
        description=(
            "Retorna apenas as importações cujo nome de processo é "
            "exatamente o informado."
        ),
    ),
    parametro_busca("Busca por trecho do nome ou do UUID do processo."),
    parametro_ordenacao(["nome_arquivo", "status", "criado_em"], "-criado_em"),
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
]

OPERACOES_IMPORTACAO_VAGAS = {
    "list": extend_schema(
        operation_id="listar_importacoes_vagas",
        summary="Listar importações de vagas",
        description=(
            "Lista as importações de vagas, da mais recente para a mais "
            "antiga, com paginação. Entram também as tentativas recusadas, "
            "com `status` `ERRO`."
        ),
        parameters=PARAMETROS_LISTAGEM,
        responses=respostas(
            {
                200: resposta(
                    ImportacaoArquivoVagasPaginadoSerializer,
                    "Página de importações de vagas.",
                    {"Lista paginada": EXEMPLO_PAGINA},
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Filtro `status` ou `processo_uuid` com valor inválido.",
                    {
                        "UUID malformado": {
                            "processo_uuid": ["Insira um UUID válido."]
                        }
                    },
                ),
                404: RESPOSTA_PAGINA_INEXISTENTE,
            }
        ),
    ),
    "create": extend_schema(
        operation_id="importar_vagas",
        summary="Importar arquivo de vagas",
        description=(
            "Recebe o CSV de vagas por unidade escolar e envia as vagas ao "
            "MS-Escolhas.\n\n"
            "O arquivo usa `;` como separador e o cabeçalho precisa ter "
            "exatamente as colunas do layout `VAGAS` mais recente: coluna "
            "a mais ou a menos invalida o arquivo. As linhas seguem para o "
            "MS-Escolhas sem validação neste serviço.\n\n"
            "Toda tentativa grava um registro de importação. Se o arquivo "
            "é recusado ou o envio falha, a resposta é 400, o registro "
            "fica com `status` `ERRO` e os motivos ficam em `erros`. Com "
            "sucesso a resposta é 201, mas o registro continua com "
            "`status` `PENDENTE`.\n\n"
            "Cabeçalho do layout cadastrado na instalação:\n\n"
            f"```\n{CABECALHO_VAGAS}\n```"
        ),
        request={MULTIPART: ImportacaoArquivoVagasCreateSerializer},
        examples=exemplos_requisicao(
            {"Arquivo e processo": EXEMPLO_FORMULARIO}, MULTIPART
        ),
        responses=respostas(
            {
                201: resposta(
                    ImportacaoArquivoVagasListSerializer,
                    (
                        "Arquivo aceito e vagas enviadas ao MS-Escolhas. "
                        "Nesta resposta `arquivo` vem como caminho relativo."
                    ),
                    {
                        "Importação aceita": {
                            **EXEMPLO_IMPORTACAO,
                            "arquivo": "/media/importacoes/vagas.csv",
                        }
                    },
                ),
                400: resposta(
                    ERRO_REQUISICAO_IMPORTACAO,
                    (
                        "Formulário inválido, arquivo recusado ou falha ao "
                        "enviar ao MS-Escolhas."
                    ),
                    {
                        "Formulário inválido": {
                            "arquivo": ["Nenhum arquivo foi submetido."]
                        },
                        "Colunas diferentes do layout": {
                            "detail": "Colunas inválidas no arquivo CSV",
                            "detalhes": (
                                "Colunas não esperadas: ['EXTRA'] | Colunas "
                                "esperadas para Vagas: ['CODCAR', 'CODLOC', "
                                "'DATA', 'DESCAR', 'STATUS', 'VGDEF', "
                                "'VGPREC'] | Encontradas: ['CODCAR', "
                                "'CODLOC', 'DATA', 'DESCAR', 'EXTRA', "
                                "'STATUS', 'VGDEF', 'VGPREC']"
                            ),
                        },
                        "Tipo de unidade desabilitado": {
                            "detail": (
                                "Tipo de unidade 'CEI' da escola EOL "
                                "094765 está desabilitado."
                            ),
                            "code": "TIPO_UE_DESABILITADO",
                        },
                        "MS-Escolhas respondeu com erro": {
                            "detail": "Falha ao enviar vagas para API externa",
                            "detalhes": "Status 502",
                            "status_code": 502,
                        },
                    },
                ),
            }
        ),
    ),
    **operacoes_de_registro(
        recurso="de vagas",
        identificador="vagas",
        modelo=ImportacaoArquivoVagas,
        parametro=PARAMETRO_ID,
        serializer_detalhe=ImportacaoArquivoVagasListSerializer,
        serializer_edicao=ImportacaoArquivoVagasCreateSerializer,
        exemplo_detalhe=EXEMPLO_IMPORTACAO,
        exemplo_edicao=EXEMPLO_EDICAO,
        exemplo_substituicao=EXEMPLO_FORMULARIO,
        exemplo_alteracao={"processo_nome": NOME_PROCESSO_EXEMPLO},
    ),
    "download_erros": operacao_baixar_erros("vagas", "vagas"),
}

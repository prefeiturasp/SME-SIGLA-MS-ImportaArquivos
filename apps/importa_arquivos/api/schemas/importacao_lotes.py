"""Documentação OpenAPI das operações de importação de lotes."""

from __future__ import annotations

from core.openapi import (
    NOME_CONCURSO_EXEMPLO,
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
    RESPOSTA_PAGINA_INEXISTENTE,
    TAMANHO_PAGINA_PADRAO,
    UUID_CONCURSO_EXEMPLO,
    exemplos_requisicao,
    parametro_busca,
    parametro_ordenacao,
    parametro_uuid,
    resposta,
    respostas,
)
from core.serializers import (
    ErroProcessamentoSerializer,
    ErrosValidacaoSerializer,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
)

from importa_arquivos.api.schemas.comuns import (
    MULTIPART,
    PARAMETRO_NOME_ARQUIVO,
    PARAMETRO_STATUS,
    operacoes_de_registro,
)
from importa_arquivos.models import ImportacaoLotes
from importa_arquivos.serializers import (
    ImportacaoLotesCreateSerializer,
    ImportacaoLotesListSerializer,
    ImportacaoLotesPaginadoSerializer,
)

TAG_IMPORTACAO_LOTES = "Importação de lotes"

CABECALHO_LOTES = (
    "LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC"
)

EXEMPLO_FORMULARIO = {
    "arquivo": "lote_7.txt",
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
}

EXEMPLO_EDICAO = {
    "arquivo": "http://localhost:8000/media/importacoes/lote_7.txt",
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
}

EXEMPLO_IMPORTACAO = {
    "uuid": "9d8c7b6a-5f4e-4d3c-8b2a-1f0e9d8c7b6a",
    "nome_arquivo": "lote_7.txt",
    "arquivo": "http://localhost:8000/media/importacoes/lote_7.txt",
    "tipo": "LOTES",
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
    "status": "CONCLUIDO",
    "total_atualizados": 1,
    "erros": None,
    "detalhes": [
        {
            "lote": 7,
            "empresa": "1",
            "vaga": "V1",
            "identificacao": 10,
            "chave_inscrito": "K",
            "numfunc": 1,
            "numvinc": None,
        }
    ],
    "criado_em": "2026-09-20T11:00:00-03:00",
    "atualizado_em": "2026-09-20T11:00:02-03:00",
}

EXEMPLO_PAGINA = {
    "links": {"next": None, "previous": None},
    "count": 1,
    "page": 1,
    "page_size": TAMANHO_PAGINA_PADRAO,
    "results": [EXEMPLO_IMPORTACAO],
}

ERRO_REQUISICAO_LOTES = PolymorphicProxySerializer(
    component_name="ErroRequisicaoImportacaoLotes",
    serializers=[ErrosValidacaoSerializer, ErroProcessamentoSerializer],
    resource_type_field_name=None,
    many=False,
)

PARAMETRO_UUID = parametro_uuid("UUID da importação de lotes.")

PARAMETROS_LISTAGEM = [
    PARAMETRO_NOME_ARQUIVO,
    PARAMETRO_STATUS,
    OpenApiParameter(
        name="concurso_uuid",
        type=OpenApiTypes.UUID,
        description="Retorna apenas as importações do concurso informado.",
    ),
    OpenApiParameter(
        name="concurso_nome",
        type=OpenApiTypes.STR,
        description=(
            "Retorna apenas as importações cujo nome de concurso é "
            "exatamente o informado."
        ),
    ),
    parametro_busca("Busca por trecho do nome ou do UUID do concurso."),
    parametro_ordenacao(["nome_arquivo", "status", "criado_em"], "-criado_em"),
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
]

OPERACOES_IMPORTACAO_LOTES = {
    "list": extend_schema(
        operation_id="listar_importacoes_lotes",
        summary="Listar importações de lotes",
        description=(
            "Lista as importações de lotes, da mais recente para a mais "
            "antiga, com paginação. Entram também as tentativas recusadas, "
            "com `status` `ERRO`."
        ),
        parameters=PARAMETROS_LISTAGEM,
        responses=respostas(
            {
                200: resposta(
                    ImportacaoLotesPaginadoSerializer,
                    "Página de importações de lotes.",
                    {"Lista paginada": EXEMPLO_PAGINA},
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Filtro `status` ou `concurso_uuid` com valor inválido.",
                    {
                        "UUID malformado": {
                            "concurso_uuid": ["Insira um UUID válido."]
                        }
                    },
                ),
                404: RESPOSTA_PAGINA_INEXISTENTE,
            }
        ),
    ),
    "create": extend_schema(
        operation_id="importar_lotes",
        summary="Importar arquivo de lotes",
        description=(
            "Recebe o TXT de lotes do SIGPEC e atualiza os habilitados do "
            "concurso no MS-Candidatos.\n\n"
            "O arquivo usa `;` como separador e precisa trazer o cabeçalho "
            "abaixo. Cada linha é validada, e os erros de todas as linhas "
            "vêm juntos em `detail`, um por linha de texto. Linhas em "
            "branco são ignoradas.\n\n"
            f"```\n{CABECALHO_LOTES}\n```\n\n"
            "`LOTE`, `IDENTIFICACAO` e `NUMFUNC` são números inteiros, "
            "`EMPRESA` e `VAGA` não podem ficar vazios, e `CHAVE_INSCRITO` "
            "e `NUMVINC` são opcionais. Todas as linhas precisam ser do "
            "mesmo lote.\n\n"
            "Toda tentativa grava um registro de importação. Se o arquivo "
            "é recusado ou o MS-Candidatos falha, a resposta é 400 e o "
            "registro fica com `status` `ERRO`. Com sucesso, o registro "
            "passa a `CONCLUIDO`, com as linhas enviadas em `detalhes`."
        ),
        request={MULTIPART: ImportacaoLotesCreateSerializer},
        examples=exemplos_requisicao(
            {"Arquivo e concurso": EXEMPLO_FORMULARIO}, MULTIPART
        ),
        responses=respostas(
            {
                201: resposta(
                    ImportacaoLotesListSerializer,
                    (
                        "Arquivo aceito e lotes gravados no MS-Candidatos. "
                        "Nesta resposta `arquivo` vem como caminho relativo."
                    ),
                    {
                        "Importação concluída": {
                            **EXEMPLO_IMPORTACAO,
                            "arquivo": "/media/importacoes/lote_7.txt",
                        }
                    },
                ),
                400: resposta(
                    ERRO_REQUISICAO_LOTES,
                    (
                        "Formulário inválido, arquivo recusado ou falha ao "
                        "gravar no MS-Candidatos."
                    ),
                    {
                        "Formulário inválido": {
                            "arquivo": ["Nenhum arquivo foi submetido."],
                            "concurso_uuid": ["Este campo é obrigatório."],
                        },
                        "Cabeçalho incompleto": {
                            "mensagem": (
                                "Cabecalho invalido para importacao de lotes."
                            ),
                            "detail": (
                                "Colunas ausentes: ['CHAVE_INSCRITO', "
                                "'IDENTIFICACAO', 'NUMFUNC', 'NUMVINC', "
                                "'VAGA']. Esperado: ['CHAVE_INSCRITO', "
                                "'EMPRESA', 'IDENTIFICACAO', 'LOTE', "
                                "'NUMFUNC', 'NUMVINC', 'VAGA']."
                            ),
                        },
                        "Linhas recusadas": {
                            "mensagem": "Erro ao validar os dados do arquivo.",
                            "detail": (
                                "Linha: 2 | Identificacao: abc - Campo "
                                "'identificacao': Input should be a valid "
                                "integer, unable to parse string as an "
                                "integer"
                            ),
                        },
                        "Falha no MS-Candidatos": {
                            "mensagem": (
                                "Erro ao fazer request para salvar os "
                                "lotes no serviço de candidatos."
                            ),
                            "detail": (
                                "Serviço de candidatos (salvar-lotes) "
                                "indisponível."
                            ),
                        },
                    },
                ),
            }
        ),
    ),
    **operacoes_de_registro(
        recurso="de lotes",
        identificador="lotes",
        modelo=ImportacaoLotes,
        parametro=PARAMETRO_UUID,
        serializer_detalhe=ImportacaoLotesListSerializer,
        serializer_edicao=ImportacaoLotesCreateSerializer,
        exemplo_detalhe=EXEMPLO_IMPORTACAO,
        exemplo_edicao=EXEMPLO_EDICAO,
        exemplo_substituicao=EXEMPLO_FORMULARIO,
        exemplo_alteracao={"concurso_nome": NOME_CONCURSO_EXEMPLO},
    ),
}

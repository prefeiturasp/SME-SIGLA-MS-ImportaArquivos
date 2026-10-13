"""Documentação OpenAPI das operações de importação de habilitados."""

from __future__ import annotations

from core.openapi import (
    NOME_CONCURSO_EXEMPLO,
    UUID_CONCURSO_EXEMPLO,
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
    EXEMPLO_ERRO_DA_IMPORTACAO,
    MULTIPART,
    PARAMETRO_NOME_ARQUIVO,
    PARAMETRO_STATUS,
    operacao_baixar_erros,
    operacoes_de_registro,
)
from importa_arquivos.api.schemas.layout import CABECALHO_HABILITADOS
from importa_arquivos.models import ImportacaoArquivoHabilitado
from importa_arquivos.serializers import (
    ImportacaoArquivoHabilitadosCreateSerializer,
    ImportacaoArquivoHabilitadosListSerializer,
)

TAG_IMPORTACAO_HABILITADOS = "Importação de habilitados"

EXEMPLO_FORMULARIO = {
    "arquivo": "habilitados.csv",
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
    "observacao": "1ª carga de habilitados",
    "mandado_judicial": False,
}

EXEMPLO_EDICAO = {
    "arquivo": "http://localhost:8000/media/importacoes/habilitados.csv",
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
    "observacao": "1ª carga de habilitados",
}

EXEMPLO_IMPORTACAO = {
    "uuid": "6b1f0c3a-2d4e-4f5a-9b7c-8d9e0f1a2b3c",
    "nome_arquivo": "habilitados.csv",
    "arquivo": "http://localhost:8000/media/importacoes/habilitados.csv",
    "status": "CONCLUIDO",
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
    "observacao": "1ª carga de habilitados",
    "quantidade": 1500,
    "criado_em": "2026-09-12T14:20:00-03:00",
    "atualizado_em": "2026-09-12T14:20:07-03:00",
    "erros": None,
}

EXEMPLO_IMPORTACAO_RECUSADA = {
    **EXEMPLO_IMPORTACAO,
    "status": "ERRO",
    "quantidade": None,
    "erros": [EXEMPLO_ERRO_DA_IMPORTACAO],
}

PARAMETRO_ID = parametro_id("da importação")

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
]

OPERACOES_IMPORTACAO_HABILITADOS = {
    "list": extend_schema(
        operation_id="listar_importacoes_habilitados",
        summary="Listar importações de habilitados",
        description=(
            "Lista as importações de habilitados, da mais recente para a "
            "mais antiga, sem paginação. Entram também as tentativas "
            "recusadas, com `status` `ERRO`."
        ),
        parameters=PARAMETROS_LISTAGEM,
        responses=respostas(
            {
                200: resposta(
                    ImportacaoArquivoHabilitadosListSerializer(many=True),
                    "Importações de habilitados.",
                    {
                        "Importação concluída": EXEMPLO_IMPORTACAO,
                        "Importação recusada": EXEMPLO_IMPORTACAO_RECUSADA,
                    },
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
            }
        ),
    ),
    "create": extend_schema(
        operation_id="importar_habilitados",
        summary="Importar arquivo de habilitados",
        description=(
            "Recebe o CSV de habilitados de um concurso, valida e envia os "
            "candidatos ao MS-Candidatos.\n\n"
            "O cabeçalho do arquivo precisa ter exatamente as colunas do "
            "layout `HABILITADOS` mais recente. Depois cada linha é "
            "validada: colunas que o layout marca como obrigatórias, CPF, "
            "e-mail, data de nascimento no formato `mm/dd/aaaa` e e-mail "
            "repetido com CPFs diferentes. O `Codigo_do_Cargo` de cada "
            "linha é conferido contra os cargos do concurso no "
            "MS-Concursos.\n\n"
            "Toda tentativa grava um registro de importação. Se o arquivo "
            "é recusado ou o envio falha, a resposta é 400, o registro "
            "fica com `status` `ERRO` e os motivos ficam em `erros`. Com "
            "sucesso, o registro passa a `CONCLUIDO`.\n\n"
            "Cabeçalho do layout cadastrado na instalação:\n\n"
            f"```\n{CABECALHO_HABILITADOS}\n```"
        ),
        request={MULTIPART: ImportacaoArquivoHabilitadosCreateSerializer},
        examples=exemplos_requisicao(
            {"Arquivo e concurso": EXEMPLO_FORMULARIO}, MULTIPART
        ),
        responses=respostas(
            {
                201: resposta(
                    ImportacaoArquivoHabilitadosListSerializer,
                    (
                        "Arquivo aceito e candidatos enviados ao "
                        "MS-Candidatos. Nesta resposta `arquivo` vem como "
                        "caminho relativo."
                    ),
                    {
                        "Importação concluída": {
                            **EXEMPLO_IMPORTACAO,
                            "arquivo": "/media/importacoes/habilitados.csv",
                        }
                    },
                ),
                400: resposta(
                    ERRO_REQUISICAO_IMPORTACAO,
                    (
                        "Formulário inválido, arquivo recusado ou falha ao "
                        "consultar o MS-Concursos ou enviar ao "
                        "MS-Candidatos."
                    ),
                    {
                        "Formulário inválido": {
                            "arquivo": ["Nenhum arquivo foi submetido."],
                            "concurso_uuid": ["Este campo é obrigatório."],
                        },
                        "Colunas diferentes do layout": {
                            "detail": "Arquivo de Habilitados inválido",
                            "detalhes": (
                                "Encontradas: ['Inscricao', 'Nome'] | "
                                "Esperadas: ['CPF', 'Codigo_do_Cargo', "
                                "'Email', 'Nome']"
                            ),
                        },
                        "Linhas recusadas": {
                            "detail": "Erros de validação encontrados",
                            "detalhes": (
                                "Linha 2: CPF inválido -> '123'; "
                                "Codigo_do_Cargo '9999' não possui relação "
                                "com o concurso selecionado. Códigos "
                                "válidos: 3859"
                            ),
                        },
                        "Concurso não encontrado": {
                            "detail": "Concurso não encontrado.",
                            "detalhes": (
                                f"Concurso UUID '{UUID_CONCURSO_EXEMPLO}' "
                                "não encontrado na API de concursos."
                            ),
                        },
                        "MS-Candidatos respondeu com erro": {
                            "detail": (
                                "Falha ao enviar candidatos para API externa"
                            ),
                            "detalhes": "Status 502",
                            "status_code": 502,
                        },
                    },
                ),
            }
        ),
    ),
    **operacoes_de_registro(
        recurso="de habilitados",
        identificador="habilitados",
        modelo=ImportacaoArquivoHabilitado,
        parametro=PARAMETRO_ID,
        serializer_detalhe=ImportacaoArquivoHabilitadosListSerializer,
        serializer_edicao=ImportacaoArquivoHabilitadosCreateSerializer,
        exemplo_detalhe=EXEMPLO_IMPORTACAO_RECUSADA,
        exemplo_edicao=EXEMPLO_EDICAO,
        exemplo_substituicao=EXEMPLO_FORMULARIO,
        exemplo_alteracao={"observacao": "Carga refeita após retificação"},
    ),
    "download_erros": operacao_baixar_erros("habilitados", "habilitados"),
}

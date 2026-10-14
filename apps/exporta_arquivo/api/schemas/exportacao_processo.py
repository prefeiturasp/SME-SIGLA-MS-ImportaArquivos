"""Documentação OpenAPI das exportações por processo e cargo.

As exportações de vagas SIGPEC, de vagas por processo e de candidatos por
processo usam a mesma view base e têm as mesmas sete operações. A função
deste módulo monta o mapa de cada uma.
"""

from __future__ import annotations

from typing import Any

from core.openapi import (
    NOME_CONCURSO_EXEMPLO,
    NOME_PROCESSO_EXEMPLO,
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
    RESPOSTA_PAGINA_INEXISTENTE,
    TAMANHO_PAGINA_PADRAO,
    TEXTO,
    UUID_CONCURSO_EXEMPLO,
    UUID_PROCESSO_EXEMPLO,
    exemplos_requisicao,
    parametro_busca,
    parametro_ordenacao,
    parametro_uuid,
    resposta,
    resposta_arquivo,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import (
    ErroDetalheSerializer,
    ErroProcessamentoSerializer,
    ErrosValidacaoSerializer,
)
from django.db.models import Model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
)

from exporta_arquivo.api.schemas.comuns import (
    CODIGO_CARGO_EXEMPLO,
    DESCRICAO_ARQUIVO,
    NOME_CARGO_EXEMPLO,
    UUID_CARGO_EXEMPLO,
    operacoes_de_registro,
)
from exporta_arquivo.models import (
    ExportacaoCandidatosProcesso,
    ExportacaoVagasProcesso,
    ExportacaoVagasSigpec,
)
from exporta_arquivo.serializers import (
    ExportacaoCandidatosProcessoCreateSerializer,
    ExportacaoCandidatosProcessoListSerializer,
    ExportacaoCandidatosProcessoPaginadoSerializer,
    ExportacaoVagasProcessoCreateSerializer,
    ExportacaoVagasProcessoListSerializer,
    ExportacaoVagasProcessoPaginadoSerializer,
    ExportacaoVagasSigpecCreateSerializer,
    ExportacaoVagasSigpecListSerializer,
    ExportacaoVagasSigpecPaginadoSerializer,
)

TAG_EXPORTACAO_VAGAS_SIGPEC = "Exportação de vagas SIGPEC"
TAG_EXPORTACAO_VAGAS_PROCESSO = "Exportação de vagas por processo"
TAG_EXPORTACAO_CANDIDATOS_PROCESSO = "Exportação de candidatos por processo"

EXEMPLO_DADOS = {
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "cargo_uuid": UUID_CARGO_EXEMPLO,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
    "processo_nome": NOME_PROCESSO_EXEMPLO,
    "cargo_nome": NOME_CARGO_EXEMPLO,
    "cargo_codigo": CODIGO_CARGO_EXEMPLO,
}

EXEMPLO_DADOS_CANDIDATOS = {
    **EXEMPLO_DADOS,
    "concurso_codigo": 215,
    "concurso_data_criacao": "2025-01-22T09:30:00-03:00",
}

EXEMPLO_REGISTRO = {
    "uuid": "5e4d3c2b-1a09-4f8e-9d7c-6b5a4f3e2d1c",
    "criado_em": "2026-09-18T15:40:00-03:00",
    "atualizado_em": "2026-09-18T15:40:01-03:00",
}

ARQUIVO_VAGAS_SIGPEC = (
    "@TABELA=[C_ERGON][PMSP_VAGAS_SME][1.0]\n"
    "@CHAVE=[SETOR][VARCHAR2]\n"
    "@TAG INICIO=\n"
    "@TAG FIM=\n"
    "@SEPARADOR=;\n"
    "@FORMATO DATA=DD/MM/YYYY\n"
    "@COLUNAS=[SETOR][VARCHAR2][VAGAS_DEFINITIVAS][NUMBER]"
    "[VAGAS_PRECARIAS][NUMBER]\n"
    "0094765;2;1;\n"
    "0019283;1;0;\n"
)

ARQUIVO_VAGAS_PROCESSO = "3859|094765|2|1\n3859|019283|1|0\n"

ARQUIVO_CANDIDATOS_PROCESSO = (
    "215|22/01/2025|52998224725|Maria Aparecida da Silva|17/05/1990|F|"
    "123456789|01310100|Avenida Paulista|1000||Bela Vista|São Paulo|SP|"
    "maria.silva@exemplo.test||11999990000|3859|||1||12\n"
)

ERRO_CAMPOS_OBRIGATORIOS = {
    "processo_uuid": ["Este campo é obrigatório."],
    "cargo_uuid": ["Este campo é obrigatório."],
}

ERRO_UUID_INVALIDO = {"cargo_uuid": ["Must be a valid UUID."]}

ERRO_LISTAGEM = PolymorphicProxySerializer(
    component_name="ErroListagemExportacao",
    serializers=[ErrosValidacaoSerializer, ErroDetalheSerializer],
    resource_type_field_name=None,
    many=False,
)

PARAMETROS_LISTAGEM = [
    OpenApiParameter(
        name="processo_uuid",
        type=OpenApiTypes.UUID,
        description=(
            "Retorna apenas as exportações do processo de convocação "
            "informado."
        ),
    ),
    OpenApiParameter(
        name="cargo_uuid",
        type=OpenApiTypes.UUID,
        description="Retorna apenas as exportações do cargo informado.",
    ),
    OpenApiParameter(
        name="concurso_uuid",
        type=OpenApiTypes.UUID,
        description="Retorna apenas as exportações do concurso informado.",
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
        name="cargo_codigo",
        type=OpenApiTypes.INT,
        description=(
            "Só tem efeito junto de `processo_uuid` e `cargo_uuid`, no "
            "download direto, que hoje não funciona."
        ),
    ),
    parametro_busca("Busca por trecho do nome do concurso."),
    parametro_ordenacao(
        ["criado_em", "atualizado_em", "processo_uuid", "cargo_uuid"],
        "-criado_em",
    ),
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
]


def operacoes_exportacao_processo(
    *,
    recurso: str,
    identificador: str,
    modelo: type[Model],
    serializer_criacao: Any,
    serializer_detalhe: Any,
    serializer_pagina: Any,
    exemplo_dados: dict[str, Any],
    descricao_geracao: str,
    exemplos_arquivo: dict[str, str],
    falhas_de_integracao: dict[Any, Any],
) -> dict[str, Any]:
    """Monta as sete operações de uma exportação por processo e cargo.

    Args:
        recurso: Nome do recurso no singular, com preposição (por exemplo
            ``de vagas SIGPEC``).
        identificador: Sufixo dos ``operation_id``.
        modelo: Model do registro de exportação.
        serializer_criacao: Modelo do corpo de criação e de edição.
        serializer_detalhe: Modelo do registro na listagem e no detalhe.
        serializer_pagina: Modelo da página da listagem.
        exemplo_dados: Exemplo do corpo de criação.
        descricao_geracao: Texto que diz de onde vêm os dados e o que o
            arquivo contém.
        exemplos_arquivo: Trechos do arquivo gerado, indexados pelo nome.
        falhas_de_integracao: Respostas de erro próprias da geração,
            além da validação.

    Returns:
        Mapa de ação para decorator, pronto para ``extend_schema_view``.
    """
    exemplo_detalhe = {**EXEMPLO_REGISTRO, **exemplo_dados}
    parametro = parametro_uuid(f"UUID da exportação {recurso}.")
    arquivo = resposta_arquivo(DESCRICAO_ARQUIVO, exemplos_arquivo)
    return {
        "list": extend_schema(
            operation_id=f"listar_exportacoes_{identificador}",
            summary=f"Listar exportações {recurso}",
            description=(
                f"Lista os registros de exportação {recurso}, do mais "
                "recente para o mais antigo, com paginação. Entram também "
                "as tentativas que falharam e ficaram sem arquivo.\n\n"
                "Com `processo_uuid` e `cargo_uuid` na mesma chamada, a "
                "rota não lista: tenta um download direto que hoje não "
                "funciona. Responde 400 se `cargo_codigo` não vier ou não "
                "for numérico, e 500 se vier."
            ),
            parameters=PARAMETROS_LISTAGEM,
            responses=respostas(
                {
                    200: resposta(
                        serializer_pagina,
                        "Página de registros de exportação.",
                        {
                            "Lista paginada": {
                                "links": {"next": None, "previous": None},
                                "count": 1,
                                "page": 1,
                                "page_size": TAMANHO_PAGINA_PADRAO,
                                "results": [exemplo_detalhe],
                            }
                        },
                    ),
                    400: resposta(
                        ERRO_LISTAGEM,
                        (
                            "Filtro com valor inválido, ou download direto "
                            "sem `cargo_codigo` numérico."
                        ),
                        {
                            "UUID malformado": {
                                "processo_uuid": ["Insira um UUID válido."]
                            },
                            "Download direto sem código do cargo": {
                                "detail": (
                                    "Para download direto, envie "
                                    "processo_uuid, cargo_uuid e "
                                    "cargo_codigo na query."
                                )
                            },
                        },
                    ),
                    404: RESPOSTA_PAGINA_INEXISTENTE,
                    500: resposta(
                        None,
                        (
                            "Erro inesperado no servidor. Acontece também "
                            "no download direto, quando `processo_uuid`, "
                            "`cargo_uuid` e `cargo_codigo` vêm juntos. O "
                            "corpo não segue um modelo JSON."
                        ),
                    ),
                }
            ),
        ),
        "create": extend_schema(
            operation_id=f"exportar_{identificador}",
            summary=f"Gerar exportação {recurso}",
            description=(
                f"{descricao_geracao}\n\n"
                "A resposta de sucesso é o próprio arquivo, com código "
                "200. O registro da exportação fica gravado e o arquivo "
                "pode ser baixado de novo pela rota de download. Toda "
                "chamada com dados válidos grava um registro, mesmo quando "
                "a geração falha; nesse caso ele fica sem arquivo.\n\n"
                "Só `processo_uuid` e `cargo_uuid` são obrigatórios."
            ),
            request=serializer_criacao,
            examples=exemplos_requisicao({"Processo e cargo": exemplo_dados}),
            responses=respostas(
                {
                    (200, TEXTO): arquivo,
                    400: resposta(
                        ErrosValidacaoSerializer,
                        "Dados inválidos.",
                        {
                            "Campos obrigatórios ausentes": (
                                ERRO_CAMPOS_OBRIGATORIOS
                            )
                        },
                    ),
                    **falhas_de_integracao,
                }
            ),
        ),
        **operacoes_de_registro(
            recurso=recurso,
            identificador=identificador,
            modelo=modelo,
            parametro=parametro,
            serializer_detalhe=serializer_detalhe,
            serializer_edicao=serializer_criacao,
            exemplo_detalhe=exemplo_detalhe,
            exemplo_edicao=exemplo_dados,
            exemplo_alteracao={"cargo_nome": NOME_CARGO_EXEMPLO},
            exemplo_incompleto=ERRO_CAMPOS_OBRIGATORIOS,
            exemplo_invalido=ERRO_UUID_INVALIDO,
        ),
        "download": extend_schema(
            operation_id=f"baixar_exportacao_{identificador}",
            summary=f"Baixar o arquivo de uma exportação {recurso}",
            description=(
                "Devolve o arquivo guardado no registro, com o mesmo "
                "conteúdo e o mesmo nome da geração original. Se a "
                "geração falhou e o registro ficou sem arquivo, a chamada "
                "termina em erro 500."
            ),
            parameters=[parametro],
            responses=respostas(
                {
                    (200, TEXTO): arquivo,
                    404: resposta_nao_encontrado(modelo),
                    500: resposta(
                        None,
                        (
                            "Erro inesperado no servidor. Acontece também "
                            "quando o registro não tem arquivo. O corpo "
                            "não segue um modelo JSON."
                        ),
                    ),
                }
            ),
        ),
    }


def _falha(descricao: str, nome: str, mensagem: str, detalhe: str) -> Any:
    """Monta uma resposta de falha com ``mensagem`` e ``detail``."""
    return resposta(
        ErroProcessamentoSerializer,
        descricao,
        {nome: {"mensagem": mensagem, "detail": detalhe}},
    )


FALHAS_VAGAS = {
    500: _falha(
        (
            "Erro inesperado ao gerar o arquivo. Acontece, por exemplo, "
            "quando o MS-Escolhas não devolve nenhuma vaga; `detail` traz "
            "o texto do erro."
        ),
        "Nenhuma vaga devolvida",
        "Erro interno ao gerar exportação.",
        (
            "{'vagas': [ErrorDetail(string='Pelo menos uma vaga deve ser "
            "enviada.', code='invalid')]}"
        ),
    ),
    502: _falha(
        "O MS-Escolhas não respondeu ou respondeu com erro.",
        "MS-Escolhas indisponível",
        "Serviço de vagas por escola indisponível.",
        "Status 503",
    ),
}

FALHAS_CANDIDATOS = {
    404: _falha(
        "Concurso ou habilitados não encontrados nos outros serviços.",
        "Concurso não encontrado",
        "Concurso não encontrado.",
        f"concurso_uuid={UUID_CONCURSO_EXEMPLO}",
    ),
    500: _falha(
        (
            "Erro inesperado ao gerar o arquivo. Acontece, por exemplo, "
            "quando o MS-Concursos devolve a data de criação do concurso "
            "fora do formato; `detail` traz o texto do erro."
        ),
        "Data do concurso fora do formato",
        "Erro interno ao gerar exportação.",
        (
            "['O valor “data-invalida” tem um formato inválido. Deve estar "
            "no formato YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ].']"
        ),
    ),
    502: _falha(
        (
            "O MS-Concursos ou o MS-Candidatos não respondeu ou respondeu "
            "com erro."
        ),
        "MS-Candidatos indisponível",
        "Serviço de candidatos (habilitados) indisponível.",
        "Status 503",
    ),
}

OPERACOES_EXPORTACAO_VAGAS_SIGPEC = operacoes_exportacao_processo(
    recurso="de vagas SIGPEC",
    identificador="vagas_sigpec",
    modelo=ExportacaoVagasSigpec,
    serializer_criacao=ExportacaoVagasSigpecCreateSerializer,
    serializer_detalhe=ExportacaoVagasSigpecListSerializer,
    serializer_pagina=ExportacaoVagasSigpecPaginadoSerializer,
    exemplo_dados=EXEMPLO_DADOS,
    descricao_geracao=(
        "Busca no MS-Escolhas as vagas do processo para o cargo "
        "(`cargo_codigo`) e gera o arquivo no formato do SIGPEC: as linhas "
        "de cabeçalho e, para cada unidade escolar, uma linha com código "
        "de integração, vagas definitivas e vagas precárias, separados "
        "por `;`. Unidades sem código de integração ficam de fora. O nome "
        "do arquivo é montado com `cargo_nome`, `cargo_codigo` e "
        "`processo_nome`."
    ),
    exemplos_arquivo={"Vagas no formato SIGPEC": ARQUIVO_VAGAS_SIGPEC},
    falhas_de_integracao=FALHAS_VAGAS,
)

OPERACOES_EXPORTACAO_VAGAS_PROCESSO = operacoes_exportacao_processo(
    recurso="de vagas por processo",
    identificador="vagas_processo",
    modelo=ExportacaoVagasProcesso,
    serializer_criacao=ExportacaoVagasProcessoCreateSerializer,
    serializer_detalhe=ExportacaoVagasProcessoListSerializer,
    serializer_pagina=ExportacaoVagasProcessoPaginadoSerializer,
    exemplo_dados=EXEMPLO_DADOS,
    descricao_geracao=(
        "Busca no MS-Escolhas as vagas do processo para o cargo "
        "(`cargo_codigo`) e gera um arquivo com uma linha por unidade "
        "escolar: código do cargo, código EOL da unidade, vagas "
        "definitivas e vagas precárias, separados por `|`. O nome do "
        "arquivo é montado com `cargo_nome`, `cargo_codigo` e "
        "`processo_nome`."
    ),
    exemplos_arquivo={"Vagas por unidade": ARQUIVO_VAGAS_PROCESSO},
    falhas_de_integracao=FALHAS_VAGAS,
)

OPERACOES_EXPORTACAO_CANDIDATOS_PROCESSO = operacoes_exportacao_processo(
    recurso="de candidatos por processo",
    identificador="candidatos_processo",
    modelo=ExportacaoCandidatosProcesso,
    serializer_criacao=ExportacaoCandidatosProcessoCreateSerializer,
    serializer_detalhe=ExportacaoCandidatosProcessoListSerializer,
    serializer_pagina=ExportacaoCandidatosProcessoPaginadoSerializer,
    exemplo_dados=EXEMPLO_DADOS_CANDIDATOS,
    descricao_geracao=(
        "Busca no MS-Concursos o código e a data de criação do concurso "
        "e, no MS-Candidatos, os habilitados do processo para o cargo "
        "(`cargo_codigo`). Gera um arquivo com uma linha por candidato, "
        "com os dados cadastrais separados por `|`, na ordem da "
        "classificação de escolha. Sem habilitados, o arquivo vem vazio. O "
        "nome do arquivo é montado com `cargo_nome` e o código do "
        "concurso.\n\n"
        "`concurso_uuid` é opcional no corpo, mas sem ele a geração "
        "termina em 404, porque a consulta ao MS-Concursos não encontra o "
        "concurso."
    ),
    exemplos_arquivo={"Um candidato": ARQUIVO_CANDIDATOS_PROCESSO},
    falhas_de_integracao=FALHAS_CANDIDATOS,
)

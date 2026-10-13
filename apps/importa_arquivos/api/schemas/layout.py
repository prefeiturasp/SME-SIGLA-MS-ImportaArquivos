"""Documentação OpenAPI das operações de layouts de importação."""

from __future__ import annotations

from core.openapi import (
    CSV,
    PARAMETRO_PAGINA_PADRAO,
    RESPOSTA_PAGINA_INEXISTENTE,
    exemplos_requisicao,
    parametro_busca,
    parametro_id,
    parametro_ordenacao,
    resposta,
    resposta_arquivo,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from importa_arquivos.models.constants import CHOICES_TIPO_IMPORTACAO_ARQUIVO
from importa_arquivos.models.layout import LayoutArquivoImportacao
from importa_arquivos.serializers import (
    LayoutArquivoImportacaoPaginadoSerializer,
    LayoutArquivoImportacaoSerializer,
)

TAG_LAYOUTS = "Layouts de importação"

TIPOS_DE_LAYOUT = [codigo for codigo, _ in CHOICES_TIPO_IMPORTACAO_ARQUIVO]

CABECALHO_HABILITADOS = (
    "Inscricao,Nome,DataNascimento,Sexo,RG,CPF,adregistroFuncional,"
    "adNumVinculo,EndLogradouro,Numero,Complemento,Bairro,Cep,Cidade,UF,"
    "telefone,celular,Email,Pontos,Classificação,Classificação_Deficiente,"
    "classNNA,Opção de Concurso,Codigo_do_Cargo,Descrição_do_Cargo,"
    "ANO_do_Concurso,Observacao,cota,Df"
)
CABECALHO_VAGAS = "DATA;CODCAR;DESCAR;CODLOC;VGPREC;VGDEF;STATUS"

EXEMPLO_ESTRUTURA = [
    {
        "key": "1",
        "campo": "Código de inscrição",
        "ordem": 1,
        "coluna": "Inscricao",
        "tamanho": 8,
        "tipoDado": "Texto",
        "campo_payload": "codigo_inscricao",
        "regrasValidacao": "campo obrigatório",
    },
    {
        "key": "2",
        "campo": "Nome",
        "ordem": 2,
        "coluna": "Nome",
        "tamanho": 40,
        "tipoDado": "Texto",
        "campo_payload": "nome",
        "regrasValidacao": "campo obrigatório",
    },
]

EXEMPLO_DADOS_LAYOUT = {"tipo": "HABILITADOS", "estrutura": EXEMPLO_ESTRUTURA}

EXEMPLO_LAYOUT = {
    "uuid": "3f2e1d0c-9b8a-4c7d-8e6f-5a4b3c2d1e0f",
    **EXEMPLO_DADOS_LAYOUT,
    "criado_em": "2026-03-02T10:00:00-03:00",
    "atualizado_em": "2026-03-02T10:00:00-03:00",
}

EXEMPLO_PAGINA = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [EXEMPLO_LAYOUT],
}

PARAMETRO_ID = parametro_id("do layout")

PARAMETRO_TIPO = OpenApiParameter(
    name="tipo",
    type=OpenApiTypes.STR,
    enum=TIPOS_DE_LAYOUT,
    description="Retorna apenas os layouts do tipo informado.",
)

RESPOSTA_LAYOUT = resposta(
    LayoutArquivoImportacaoSerializer,
    "Layout.",
    {"Layout de habilitados": EXEMPLO_LAYOUT},
)

RESPOSTA_NAO_ENCONTRADO = resposta_nao_encontrado(LayoutArquivoImportacao)

RESPOSTA_DADOS_INVALIDOS = resposta(
    ErrosValidacaoSerializer,
    "Dados inválidos.",
    {
        "Tipo inexistente e estrutura ausente": {
            "tipo": ['"X" não é um escolha válido.'],
            "estrutura": ["Este campo é obrigatório."],
        }
    },
)

OPERACOES_LAYOUTS = {
    "list": extend_schema(
        operation_id="listar_layouts",
        summary="Listar layouts",
        description=(
            "Lista os layouts cadastrados, do mais recente para o mais "
            "antigo, com paginação. Pode haver mais de um layout do mesmo "
            "tipo: as importações de habilitados e de vagas usam o mais "
            "recente de cada tipo."
        ),
        parameters=[
            PARAMETRO_TIPO,
            parametro_busca("Busca por trecho do tipo."),
            parametro_ordenacao(["tipo", "criado_em"], "-criado_em"),
            PARAMETRO_PAGINA_PADRAO,
        ],
        responses=respostas(
            {
                200: resposta(
                    LayoutArquivoImportacaoPaginadoSerializer,
                    "Página de layouts.",
                    {"Lista paginada": EXEMPLO_PAGINA},
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Filtro `tipo` com valor fora das opções.",
                    {
                        "Tipo inexistente": {
                            "tipo": [
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
        operation_id="criar_layout",
        summary="Criar layout",
        description=(
            "Cadastra um layout. Por ser o mais recente do tipo, ele passa "
            "a valer para as próximas importações desse tipo. O serviço não "
            "confere o conteúdo de `estrutura`."
        ),
        request=LayoutArquivoImportacaoSerializer,
        examples=exemplos_requisicao({"Novo layout": EXEMPLO_DADOS_LAYOUT}),
        responses=respostas(
            {
                201: resposta(
                    LayoutArquivoImportacaoSerializer,
                    "Layout criado.",
                    {"Layout de habilitados": EXEMPLO_LAYOUT},
                ),
                400: RESPOSTA_DADOS_INVALIDOS,
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_layout",
        summary="Detalhar layout",
        description="Retorna um layout pelo identificador numérico.",
        parameters=[PARAMETRO_ID],
        responses=respostas(
            {200: RESPOSTA_LAYOUT, 404: RESPOSTA_NAO_ENCONTRADO}
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_layout",
        summary="Atualizar layout",
        description=(
            "Substitui o tipo e a estrutura do layout. Os dois campos são "
            "obrigatórios."
        ),
        parameters=[PARAMETRO_ID],
        request=LayoutArquivoImportacaoSerializer,
        examples=exemplos_requisicao(
            {"Dados do layout": EXEMPLO_DADOS_LAYOUT}
        ),
        responses=respostas(
            {
                200: RESPOSTA_LAYOUT,
                400: RESPOSTA_DADOS_INVALIDOS,
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_layout",
        summary="Atualizar layout parcialmente",
        description="Altera apenas os campos enviados.",
        parameters=[PARAMETRO_ID],
        request=LayoutArquivoImportacaoSerializer,
        examples=exemplos_requisicao(
            {"Trocar a estrutura": {"estrutura": EXEMPLO_ESTRUTURA}}
        ),
        responses=respostas(
            {
                200: RESPOSTA_LAYOUT,
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Dados inválidos.",
                    {
                        "Tipo inexistente": {
                            "tipo": ['"X" não é um escolha válido.']
                        }
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "destroy": extend_schema(
        operation_id="excluir_layout",
        summary="Excluir layout",
        description=(
            "Exclui o layout. Se era o único do tipo, as importações desse "
            "tipo passam a ser recusadas por falta de layout."
        ),
        parameters=[PARAMETRO_ID],
        responses=respostas(
            {
                204: resposta(None, "Layout excluído."),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "download": extend_schema(
        operation_id="baixar_modelo_layout",
        summary="Baixar o modelo de arquivo de um layout",
        description=(
            "Devolve um arquivo CSV com uma única linha: o cabeçalho "
            "definido no layout mais recente do tipo informado. O separador "
            "é `;` para `VAGAS` e `,` para os demais tipos."
        ),
        parameters=[
            OpenApiParameter(
                name="tipo",
                type=OpenApiTypes.STR,
                required=True,
                enum=TIPOS_DE_LAYOUT,
                description="Tipo do layout cujo modelo será baixado.",
            )
        ],
        responses=respostas(
            {
                (200, CSV): resposta_arquivo(
                    "Arquivo CSV só com a linha de cabeçalho.",
                    {
                        "Modelo de habilitados": (
                            f"{CABECALHO_HABILITADOS}\r\n"
                        ),
                        "Modelo de vagas": f"{CABECALHO_VAGAS}\r\n",
                    },
                    CSV,
                ),
                400: resposta(
                    ErroDetalheSerializer,
                    "Parâmetro `tipo` ausente.",
                    {"Sem tipo": {"detail": "Parâmetro tipo é obrigatório."}},
                ),
                404: resposta(
                    ErroDetalheSerializer,
                    "Não há layout cadastrado para o tipo.",
                    {
                        "Sem layout": {
                            "detail": (
                                "Layout não encontrado para o tipo "
                                "informado."
                            )
                        }
                    },
                ),
            }
        ),
    ),
}

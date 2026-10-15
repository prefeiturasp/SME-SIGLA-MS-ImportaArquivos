"""Descrições dos campos expostos pela API de importação."""

from __future__ import annotations

from typing import Any

DESCRICOES_IMPORTACAO: dict[str, dict[str, Any]] = {
    "uuid": {"help_text": "Identificador da importação."},
    "nome_arquivo": {"help_text": "Nome do arquivo enviado."},
    "arquivo": {"help_text": "URL do arquivo armazenado."},
    "tipo": {"help_text": "Tipo da importação."},
    "status": {
        "help_text": (
            "Situação da importação. `ERRO` indica arquivo recusado ou "
            "falha no envio dos dados; os motivos ficam em `erros`."
        )
    },
    "concurso_uuid": {"help_text": "UUID do concurso (MS-Concursos)."},
    "concurso_nome": {
        "help_text": "Nome do concurso, gravado como foi informado."
    },
    "processo_uuid": {
        "help_text": (
            "UUID do processo de convocação (MS-ProcessosConvocacao)."
        )
    },
    "processo_nome": {
        "help_text": (
            "Nome do processo de convocação, gravado como foi informado."
        )
    },
    "observacao": {"help_text": "Texto livre sobre a importação."},
    "quantidade": {
        "help_text": "Quantidade de linhas de candidatos lidas do arquivo."
    },
    "total_atualizados": {
        "help_text": "Quantidade de candidatos atualizados no MS-Candidatos."
    },
    "detalhes": {
        "help_text": (
            "Linhas do arquivo depois de validadas, como foram enviadas ao "
            "MS-Candidatos."
        )
    },
    "processo_id": {
        "help_text": "Identificador do processo de convocação na PRODAM."
    },
    "dados_prodam": {
        "help_text": (
            "Registros devolvidos pela PRODAM "
            "(`lstDadosResultadoConvocacaoIngresso`), como vieram."
        )
    },
    "modo": {
        "help_text": (
            "Como a importação foi disparada: `MANUAL`, por esta API, ou "
            "`AUTOMATICA`, pela rotina agendada."
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última alteração do registro."
    },
}

DESCRICOES_LAYOUT: dict[str, dict[str, Any]] = {
    "uuid": {"help_text": "Identificador do layout."},
    "tipo": {"help_text": "Tipo de arquivo a que o layout se aplica."},
    "estrutura": {
        "help_text": (
            "Lista com a definição de cada coluna do arquivo. Em cada item, "
            "`coluna` é o nome esperado no cabeçalho e `campo_payload` é o "
            "nome do dado enviado ao serviço de destino. `obrigatorio` com "
            "`1` ou `true` faz a importação de habilitados recusar linhas "
            "com a coluna vazia. As demais chaves (`campo`, `ordem`, "
            "`tamanho`, `tipoDado`, `regrasValidacao`) são descritivas."
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última alteração do registro."
    },
}

DESCRICAO_ERROS = (
    "Erros registrados na importação, do mais recente para o mais antigo, "
    "ou nulo se não houve erro."
)

"""Descrições dos campos expostos pela API de exportação."""

from __future__ import annotations

from typing import Any

DESCRICOES_EXPORTACAO: dict[str, dict[str, Any]] = {
    "uuid": {"help_text": "Identificador da exportação."},
    "processo_uuid": {
        "help_text": (
            "UUID do processo de convocação (MS-ProcessosConvocacao) cujos "
            "dados são exportados."
        )
    },
    "cargo_uuid": {"help_text": "UUID do cargo (MS-Concursos)."},
    "concurso_uuid": {"help_text": "UUID do concurso (MS-Concursos)."},
    "concurso_nome": {
        "help_text": "Nome do concurso, gravado como foi informado."
    },
    "processo_nome": {
        "help_text": (
            "Nome do processo de convocação, gravado como foi informado."
        )
    },
    "cargo_nome": {"help_text": "Nome do cargo, gravado como foi informado."},
    "cargo_codigo": {
        "help_text": (
            "Código numérico do cargo, usado para buscar os dados nos "
            "outros serviços."
        )
    },
    "concurso_codigo": {
        "help_text": (
            "Código do concurso. O serviço grava aqui o valor obtido no "
            "MS-Concursos ao gerar o arquivo."
        )
    },
    "concurso_data_criacao": {
        "help_text": (
            "Data de criação do concurso. O serviço grava aqui o valor "
            "obtido no MS-Concursos ao gerar o arquivo."
        )
    },
    "numero_lote": {
        "help_text": (
            "Número do lote, usado para buscar os candidatos no "
            "MS-Candidatos."
        )
    },
    "lote_uuid": {"help_text": "UUID do lote (MS-Candidatos)."},
    "nome_arquivo": {
        "help_text": (
            "Nome do arquivo gerado, ou nulo se a exportação não gerou "
            "arquivo."
        )
    },
    "status": {
        "help_text": (
            "Situação da exportação: `SUCESSO` quando o arquivo do lote foi "
            "gerado, `ATENCAO` quando há candidatos sem escolha e o arquivo "
            "lista os pendentes, e `ERRO` quando nada foi gerado."
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última alteração do registro."
    },
}

DESCRICOES_CABECALHO: dict[str, dict[str, Any]] = {
    "uuid": {"help_text": "Identificador do cabeçalho."},
    "tabela": {"help_text": "Valor da linha `@TABELA=`."},
    "chave": {"help_text": "Valor da linha `@CHAVE=`."},
    "tag_inicio": {"help_text": "Valor da linha `@TAG INICIO=`."},
    "tag_fim": {"help_text": "Valor da linha `@TAG FIM=`."},
    "separador": {
        "help_text": (
            "Separador de colunas do arquivo, valor da linha `@SEPARADOR=`."
        )
    },
    "formato_data": {"help_text": "Valor da linha `@FORMATO DATA=`."},
    "colunas": {"help_text": "Valor da linha `@COLUNAS=`."},
    "ativo": {
        "help_text": (
            "Marca o cabeçalho como o que deve valer. Hoje a exportação de "
            "lotes grava um cabeçalho fixo e não consulta este cadastro."
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última alteração do registro."
    },
}

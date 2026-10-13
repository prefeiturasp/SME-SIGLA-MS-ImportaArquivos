"""Módulo serializers/importacao_erros."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from importa_arquivos.models import (
    ImportacaoArquivoHabilitado,
    ImportacaoArquivoVagas,
    ImportacaoErro,
    ImportacaoEscolhas,
    ImportacaoLotes,
)


class ImportacaoErrosListSerializer(serializers.Serializer):
    """Erro de uma importação, como aparece na listagem de erros."""

    concurso_uuid = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="UUID do concurso da importação. Hoje vem sempre nulo.",
    )
    processo_uuid = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="UUID do processo da importação. Hoje vem sempre nulo.",
    )
    mensagem = serializers.CharField(help_text="Resumo do erro.")
    erros = serializers.CharField(
        help_text=(
            "Detalhe do erro. Quando há mais de um motivo, eles vêm "
            "separados por ` | `."
        )
    )

    def to_representation(self, instance: ImportacaoErro) -> Any:
        """Monta a representação do erro conforme o modelo de importação."""
        data = {
            "mensagem": instance.mensagem,
            "erros": instance.erros,
            "concurso_uuid": None,
            "processo_uuid": None,
        }
        try:
            obj = instance.importacao_obj
            if obj is not None:
                if isinstance(obj, ImportacaoArquivoHabilitado):
                    data["concurso_uuid"] = obj.concurso_uuid  # type: ignore[assignment]
                elif isinstance(
                    obj, ImportacaoArquivoVagas | ImportacaoEscolhas
                ):
                    data["processo_uuid"] = obj.processo_uuid  # type: ignore[assignment]
                elif isinstance(obj, ImportacaoLotes):
                    data["concurso_uuid"] = obj.concurso_uuid  # type: ignore[assignment]
        except Exception:
            pass
        return data


class ErroDaImportacaoSerializer(serializers.Serializer):
    """Erro registrado durante uma importação."""

    mensagem = serializers.CharField(help_text="Resumo do erro.")
    erros = serializers.CharField(
        help_text=(
            "Detalhe do erro. Na validação de arquivo, traz as linhas "
            "recusadas separadas por ` | `."
        )
    )
    criado_em = serializers.DateTimeField(
        help_text="Data e hora em que o erro foi registrado."
    )


class ErroImportacaoSerializer(serializers.Serializer):
    """Arquivo recusado ou falha ao enviar os dados a outro serviço."""

    detail = serializers.CharField(help_text="Resumo da falha.")
    detalhes = serializers.CharField(
        required=False,
        help_text=(
            "Detalhe da falha: colunas ou linhas recusadas do arquivo, ou "
            "a resposta do serviço chamado."
        ),
    )
    status_code = serializers.IntegerField(
        required=False,
        help_text=(
            "Código HTTP devolvido pelo serviço chamado, quando a falha "
            "foi no envio dos dados."
        ),
    )
    code = serializers.CharField(
        required=False,
        help_text=(
            "Código da falha, quando o serviço chamado informa um, como "
            "`TIPO_UE_DESABILITADO`."
        ),
    )

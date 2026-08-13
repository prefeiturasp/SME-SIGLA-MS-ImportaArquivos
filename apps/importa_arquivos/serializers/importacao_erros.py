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
    """Serializer para listagem de erros de importação."""

    concurso_uuid = serializers.UUIDField(required=False, allow_null=True)
    processo_uuid = serializers.UUIDField(required=False, allow_null=True)
    mensagem = serializers.CharField()
    erros = serializers.CharField()

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

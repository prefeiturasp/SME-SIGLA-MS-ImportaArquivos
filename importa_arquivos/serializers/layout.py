"""Módulo serializers/layout."""

from rest_framework import serializers

from ..models.layout import LayoutArquivoImportacao


class LayoutArquivoImportacaoSerializer(serializers.ModelSerializer):
    """Serializer do modelo LayoutArquivoImportacao."""

    class Meta:
        """Representa Meta."""

        model = LayoutArquivoImportacao
        fields = ["uuid", "tipo", "estrutura", "criado_em", "atualizado_em"]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]

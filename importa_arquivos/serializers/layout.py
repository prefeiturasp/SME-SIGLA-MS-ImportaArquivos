"""Módulo serializers/layout."""

from rest_framework import serializers

from ..models.layout import LayoutArquivoImportacao


class LayoutArquivoImportacaoSerializer(serializers.ModelSerializer):
    """Define LayoutArquivoImportacaoSerializer."""

    class Meta:
        """Define Meta."""

        model = LayoutArquivoImportacao
        fields = ["uuid", "tipo", "estrutura", "criado_em", "atualizado_em"]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]

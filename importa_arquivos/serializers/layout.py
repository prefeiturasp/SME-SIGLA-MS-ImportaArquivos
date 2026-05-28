from rest_framework import serializers

from ..models.layout import LayoutArquivoImportacao


class LayoutArquivoImportacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayoutArquivoImportacao
        fields = ["uuid", "tipo", "estrutura", "criado_em", "atualizado_em"]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]

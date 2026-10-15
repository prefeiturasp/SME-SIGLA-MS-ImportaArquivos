"""Módulo serializers/layout."""

from core.serializers import PaginaPadraoSerializer
from rest_framework import serializers

from ..models.layout import LayoutArquivoImportacao
from .descricoes import DESCRICOES_LAYOUT


class LayoutArquivoImportacaoSerializer(serializers.ModelSerializer):
    """Layout de um tipo de arquivo de importação."""

    class Meta:
        """Representa Meta."""

        model = LayoutArquivoImportacao
        fields = ["uuid", "tipo", "estrutura", "criado_em", "atualizado_em"]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]
        extra_kwargs = DESCRICOES_LAYOUT


class LayoutArquivoImportacaoPaginadoSerializer(PaginaPadraoSerializer):
    """Página da listagem de layouts."""

    results = LayoutArquivoImportacaoSerializer(
        many=True, help_text="Layouts da página."
    )

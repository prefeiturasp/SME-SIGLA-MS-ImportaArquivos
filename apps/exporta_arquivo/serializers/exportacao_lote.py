"""Módulo serializers/exportacao_lote."""

from core.serializers import PaginaPadraoSerializer, PaginaSerializer
from rest_framework import serializers

from ..models import CabecalhoExportacaoLote, ExportacaoLote
from .descricoes import DESCRICOES_CABECALHO, DESCRICOES_EXPORTACAO


class ExportacaoLoteCreateSerializer(serializers.ModelSerializer):
    """Lote de candidatos a exportar."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoLote
        fields = [
            "concurso_uuid",
            "concurso_nome",
            "numero_lote",
            "lote_uuid",
        ]
        extra_kwargs = DESCRICOES_EXPORTACAO


class ExportacaoLoteListSerializer(serializers.ModelSerializer):
    """Exportação de lote, com a situação do arquivo gerado."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoLote
        fields = [
            "uuid",
            "criado_em",
            "atualizado_em",
            "concurso_uuid",
            "concurso_nome",
            "numero_lote",
            "lote_uuid",
            "nome_arquivo",
            "status",
        ]
        read_only_fields = fields
        extra_kwargs = DESCRICOES_EXPORTACAO


class CabecalhoExportacaoLoteSerializer(serializers.ModelSerializer):
    """Cabeçalho cadastrado para o arquivo de exportação de lote."""

    class Meta:
        """Representa Meta."""

        model = CabecalhoExportacaoLote
        fields = [
            "uuid",
            "criado_em",
            "atualizado_em",
            "tabela",
            "chave",
            "tag_inicio",
            "tag_fim",
            "separador",
            "formato_data",
            "colunas",
            "ativo",
        ]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]
        extra_kwargs = DESCRICOES_CABECALHO


class ExportacaoLotePaginadoSerializer(PaginaSerializer):
    """Página da listagem de exportações de lote."""

    results = ExportacaoLoteListSerializer(
        many=True, help_text="Exportações de lote da página."
    )


class CabecalhoExportacaoLotePaginadoSerializer(PaginaPadraoSerializer):
    """Página da listagem de cabeçalhos de exportação de lote."""

    results = CabecalhoExportacaoLoteSerializer(
        many=True, help_text="Cabeçalhos da página."
    )

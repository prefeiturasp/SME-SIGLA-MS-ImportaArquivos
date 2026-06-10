"""Módulo serializers/exportacao_lote."""

from rest_framework import serializers

from ..models import CabecalhoExportacaoLote, ExportacaoLote


class ExportacaoLoteCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de exportação de lote."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoLote
        fields = [
            "concurso_uuid",
            "concurso_nome",
            "numero_lote",
            "lote_uuid",
        ]


class ExportacaoLoteListSerializer(serializers.ModelSerializer):
    """Serializer para listagem e detalhe de exportações de lote."""

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


class CabecalhoExportacaoLoteSerializer(serializers.ModelSerializer):
    """Serializer para leitura e edição do cabeçalho de exportação de lote."""

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

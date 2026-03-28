from rest_framework import serializers

from ..models import ExportacaoLote, CabecalhoExportacaoLote


class ExportacaoLoteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de exportação de lote.
    O frontend envia concurso_uuid, numero_lote, opcionalmente codigo_cargo e concurso_nome.
    lote_uuid mantido para compatibilidade com registros antigos.
    """

    class Meta:
        model = ExportacaoLote
        fields = [
            "concurso_uuid",
            "concurso_nome",
            "numero_lote",          
            "lote_uuid",
        ]


class ExportacaoLoteListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem e detalhe de exportações de lote.
    """

    class Meta:
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
    """
    Serializer para leitura e edição do cabeçalho de exportação de lote.
    """

    class Meta:
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

from rest_framework import serializers
from ..models import ImportacaoLotes


class ImportacaoLotesCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de importações de lotes.
    Aceita arquivo TXT, concurso_uuid e concurso_nome.
    """

    class Meta:
        model = ImportacaoLotes
        fields = ['arquivo', 'concurso_uuid', 'concurso_nome']

    def create(self, validated_data):
        arquivo = validated_data.get('arquivo')
        nome_arquivo = getattr(arquivo, 'name', None) or 'Importação de Lotes'
        instance = ImportacaoLotes.objects.create(
            nome_arquivo=nome_arquivo,
            status='PENDENTE',
            **validated_data,
        )
        return instance


class ImportacaoLotesListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem e detalhe de importações de lotes.
    """

    class Meta:
        model = ImportacaoLotes
        fields = [
            'uuid',
            'nome_arquivo',
            'arquivo',
            'concurso_uuid',
            'concurso_nome',
            'status',
            'total_atualizados',
            'erros',
            'detalhes',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em', 'status', 'total_atualizados', 'erros', 'detalhes']

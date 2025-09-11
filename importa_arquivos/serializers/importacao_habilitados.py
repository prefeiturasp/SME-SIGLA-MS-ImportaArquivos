from rest_framework import serializers
from ..models import ImportacaoArquivoHabilitado


class ImportacaoArquivoHabilitadosCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de importações de arquivos habilitados.
    Inclui apenas campos de concurso, tipo (somente escrita) e arquivo.
    """
    class Meta:
        model = ImportacaoArquivoHabilitado
        fields = [
            'arquivo', 'concurso_uuid', 'concurso_nome'
        ]

    def create(self, validated_data):
        arquivo = validated_data.get('arquivo')
        nome_arquivo = getattr(arquivo, 'name', None) or 'Importação de Habilitados'
        instance = ImportacaoArquivoHabilitado.objects.create(
            nome_arquivo=nome_arquivo,
            tipo='HABILITADOS',
            **validated_data,
        )
        return instance


class ImportacaoArquivoHabilitadosListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem/detalhe com todos os campos do modelo.
    """
    class Meta:
        model = ImportacaoArquivoHabilitado
        fields = [
            'uuid', 'nome_arquivo', 'arquivo', 'status', 'concurso_uuid', 'concurso_nome',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


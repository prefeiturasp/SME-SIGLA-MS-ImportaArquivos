from rest_framework import serializers
from .models import ImportacaoArquivos


class ImportacaoArquivosSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ImportacaoArquivos.
    """
    class Meta:
        model = ImportacaoArquivos
        fields = ['uuid', 'nome', 'descricao', 'arquivo', 'status', 'criado_em', 'atualizado_em']
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


class ImportacaoArquivosListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de importações de arquivos.
    """
    class Meta:
        model = ImportacaoArquivos
        fields = ['uuid', 'nome', 'status', 'criado_em']


class ImportacaoArquivosSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para selects/dropdowns no frontend.
    """
    value = serializers.UUIDField(source='uuid')
    label = serializers.CharField(source='nome')
    
    class Meta:
        model = ImportacaoArquivos
        fields = ['value', 'label', 'status']

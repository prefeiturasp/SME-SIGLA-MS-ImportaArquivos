from rest_framework import serializers
from .models import ImportacaoArquivos, Layout


class ImportacaoArquivosSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ImportacaoArquivos.
    """
    arquivo = serializers.FileField(write_only=True, required=True)
    
    class Meta:
        model = ImportacaoArquivos
        fields = ['uuid', 'concurso', 'cargo', 'arquivo', 'arquivo_nome_original', 'arquivo_tamanho', 'arquivo_content_type', 'tipo_de_layout', 'status', 'criado_em', 'atualizado_em']
        read_only_fields = ['uuid', 'arquivo_nome_original', 'arquivo_tamanho', 'arquivo_content_type', 'status', 'criado_em', 'atualizado_em']
    
    def create(self, validated_data):
        arquivo = validated_data.pop('arquivo')
        importacao = ImportacaoArquivos(**validated_data)
        importacao.set_arquivo_temporario(arquivo)
        importacao.save()
        return importacao


class ImportacaoArquivosListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de importações de arquivos.
    """
    class Meta:
        model = ImportacaoArquivos
        fields = ['uuid', 'concurso', 'cargo', 'arquivo_nome_original', 'arquivo_tamanho', 'tipo_de_layout', 'status', 'criado_em']


class ImportacaoArquivosSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para selects/dropdowns no frontend.
    """
    value = serializers.UUIDField(source='uuid')
    label = serializers.SerializerMethodField()
    
    class Meta:
        model = ImportacaoArquivos
        fields = ['value', 'label', 'arquivo_nome_original', 'tipo_de_layout', 'status']
    
    def get_label(self, obj):
        return f"{obj.concurso} - {obj.cargo}"


class LayoutSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Layout.
    """
    total_campos = serializers.ReadOnlyField()
    
    class Meta:
        model = Layout
        fields = ['uuid', 'tipo_de_layout', 'dados', 'total_campos', 'criado_em', 'atualizado_em']
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']

    def validate_dados(self, value):
        """
        Valida a estrutura dos dados JSON.
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("O campo 'dados' deve ser uma lista.")
        
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(f"Item {i+1} deve ser um objeto.")
            
            required_fields = ['ordem', 'campo', 'tipo', 'tamanho', 'regras_de_validacao']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Campo obrigatório '{field}' não encontrado no item {i+1}.")
            
            # Validar tipos específicos
            if not isinstance(item['ordem'], int):
                raise serializers.ValidationError(f"Campo 'ordem' no item {i+1} deve ser um número inteiro.")
            
            if not isinstance(item['campo'], str):
                raise serializers.ValidationError(f"Campo 'campo' no item {i+1} deve ser uma string.")
            
            if not isinstance(item['tipo'], str):
                raise serializers.ValidationError(f"Campo 'tipo' no item {i+1} deve ser uma string.")
            
            if not isinstance(item['tamanho'], int):
                raise serializers.ValidationError(f"Campo 'tamanho' no item {i+1} deve ser um número inteiro.")
            
            if not isinstance(item['regras_de_validacao'], str):
                raise serializers.ValidationError(f"Campo 'regras_de_validacao' no item {i+1} deve ser uma string.")
        
        return value


class LayoutListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de layouts.
    """
    total_campos = serializers.ReadOnlyField()
    
    class Meta:
        model = Layout
        fields = ['uuid', 'tipo_de_layout', 'dados', 'total_campos', 'criado_em']


class LayoutSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para selects/dropdowns no frontend.
    """
    value = serializers.UUIDField(source='uuid')
    label = serializers.SerializerMethodField()
    
    class Meta:
        model = Layout
        fields = ['value', 'label', 'tipo_de_layout']
    
    def get_label(self, obj):
        return f"Layout {obj.tipo_de_layout} ({obj.total_campos} campos)"

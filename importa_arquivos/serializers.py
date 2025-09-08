from rest_framework import serializers
from .models import ImportacaoArquivos


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


class LayoutCreateSerializer(serializers.Serializer):
    """
    Serializer para criação/atualização de layouts.
    Aceita apenas tipo_de_layout e dados.
    """
    tipo_de_layout = serializers.CharField(max_length=50, required=True)
    dados = serializers.ListField(required=True)

    def validate_dados(self, value):
        """
        Valida a estrutura dos dados JSON.
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("O campo 'dados' deve ser uma lista.")
        
        if not value:
            raise serializers.ValidationError("Layout deve ter pelo menos um campo.")
        
        ordens_usadas = set()
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(f"Item {i+1} deve ser um objeto.")
            
            required_fields = ['ordem', 'campo', 'tipo', 'tamanho', 'regras_de_validacao']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Campo obrigatório '{field}' não encontrado no item {i+1}.")
            
            # Validar ordem única
            ordem = item.get('ordem')
            if not isinstance(ordem, int):
                raise serializers.ValidationError(f"Campo 'ordem' no item {i+1} deve ser um número inteiro.")
            
            if ordem in ordens_usadas:
                raise serializers.ValidationError(f"Ordem {ordem} está duplicada no item {i+1}.")
            ordens_usadas.add(ordem)
            
            # Validar tipos permitidos
            tipos_permitidos = ['string', 'integer', 'decimal', 'date', 'text']
            if item.get('tipo') not in tipos_permitidos:
                raise serializers.ValidationError(f"Tipo '{item.get('tipo')}' no item {i+1} não é válido. Tipos permitidos: {tipos_permitidos}")
            
            # Validar tamanho
            try:
                tamanho = int(item.get('tamanho', 0))
                if tamanho <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Campo 'tamanho' no item {i+1} deve ser um número inteiro positivo.")
        
        return value


class LayoutSerializer(serializers.Serializer):
    """
    Serializer para retorno completo de layouts (GET).
    Retorna todos os campos incluindo dados completos.
    """
    uuid = serializers.UUIDField(read_only=True)
    tipo_de_layout = serializers.CharField(read_only=True)
    dados = serializers.ListField(read_only=True)
    total_campos = serializers.IntegerField(read_only=True)
    criado_em = serializers.DateTimeField(read_only=True)


class LayoutListSerializer(serializers.Serializer):
    """
    Serializer para listagem de layouts.
    Inclui o campo dados completo com todos os subcampos.
    """
    uuid = serializers.UUIDField(read_only=True)
    tipo_de_layout = serializers.CharField(read_only=True)
    dados = serializers.ListField(read_only=True)
    total_campos = serializers.IntegerField(read_only=True)
    criado_em = serializers.DateTimeField(read_only=True)


class LayoutSelectSerializer(serializers.Serializer):
    """
    Serializer para seleção de layout (formato select).
    """
    value = serializers.UUIDField(source='uuid', read_only=True)
    label = serializers.SerializerMethodField()
    tipo_de_layout = serializers.CharField(read_only=True)
    
    def get_label(self, obj):
        total_campos = obj.get('total_campos', len(obj.get('dados', [])))
        return f"Layout {obj.get('tipo_de_layout')} ({total_campos} campos)"

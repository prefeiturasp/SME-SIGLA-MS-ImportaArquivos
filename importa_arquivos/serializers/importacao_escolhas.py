from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from ..models import ImportacaoEscolhas, ImportacaoErro
from ..models.base import CHOICES_STATUS_IMPORTACAO_ARQUIVO


class ImportacaoEscolhasCreateSerializer(serializers.Serializer):
    """Serializer de criação para importações de escolhas."""
    processo_uuid = serializers.UUIDField(required=True)
    processo_id = serializers.IntegerField(required=False, allow_null=True)
    concurso_uuid = serializers.UUIDField(required=True)


class ImportacaoEscolhasListSerializer(serializers.ModelSerializer):
    """Serializer de listagem/detalhe para importações de escolhas."""
    erros = serializers.SerializerMethodField()
    processo_nome = serializers.SerializerMethodField()
    
    _content_type_cache = None
    
    class Meta:
        model = ImportacaoEscolhas
        fields = [
            'uuid', 'processo_uuid', 'processo_id', 'dados_prodam',
            'status', 'criado_em', 'atualizado_em', 'erros', 'concurso_uuid',
            'processo_nome'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em', 'erros', 'processo_nome']
    
    def get_erros(self, obj):
        """Retorna os erros associados à importação, se existirem."""
        if ImportacaoEscolhasListSerializer._content_type_cache is None:
            ImportacaoEscolhasListSerializer._content_type_cache = ContentType.objects.get_for_model(ImportacaoEscolhas)
        
        erros_queryset = ImportacaoErro.objects.filter(
            content_type=ImportacaoEscolhasListSerializer._content_type_cache,
            object_id=obj.uuid
        ).order_by('-criado_em')
        
        if not erros_queryset.exists():
            return None
        
        erros_list = []
        for erro in erros_queryset:
            erros_list.append({
                'mensagem': erro.mensagem,
                'erros': erro.erros,
                'criado_em': erro.criado_em
            })
        
        return erros_list
    
    def get_processo_nome(self, obj):
        """Retorna o nome do processo buscando via API externa se necessário."""
        # O frontend já busca o nome do processo quando necessário
        # Este campo pode ser None e o frontend fará a busca
        return None


class ResponseSerializer(serializers.Serializer):
    """Serializer para validar resposta da API externa."""
    retorno = serializers.CharField(required=True)
    mensagem = serializers.CharField(required=True)
    lstDadosResultadoConvocacaoIngresso = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        allow_empty=True
    )

    def validate_lstDadosResultadoConvocacaoIngresso(self, value):
        """Valida estrutura dos dados de resultado."""
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Cada item deve ser um dicionário")
            
            required_fields = ['codigoPessoaFisica', 'codigoCargo', 'descricaoStatus']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Campo obrigatório ausente: {field}")
        
        return value


class EscolhaItemSerializer(serializers.Serializer):
    """Serializer para item de escolha."""
    codigoPessoaFisica = serializers.CharField()
    codigoCargo = serializers.CharField()
    codigoUnidadeAlocacao = serializers.CharField(allow_null=True, required=False)
    tipoVaga = serializers.CharField(allow_null=True, required=False)
    descricaoStatus = serializers.CharField()


class EscolhasImportacaoSerializer(serializers.Serializer):
    """Serializer para enviar dados ao MS-Escolhas."""
    processo_uuid = serializers.UUIDField(required=True)
    concurso_uuid = serializers.UUIDField(required=True)
    escolhas = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate_escolhas(self, value):
        """Valida estrutura das escolhas."""
        for escolha in value:
            required_fields = ['cpf', 'codigo_cargo', 'situacao']
            for field in required_fields:
                if field not in escolha:
                    raise serializers.ValidationError(f"Campo obrigatório ausente na escolha: {field}")
        return value


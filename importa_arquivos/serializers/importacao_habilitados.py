from rest_framework import serializers
from ..models import ImportacaoArquivoHabilitado
from django.contrib.contenttypes.models import ContentType
from ..models import ImportacaoErro


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
    erros = serializers.SerializerMethodField()
    
    _content_type_cache = None
    
    class Meta:
        model = ImportacaoArquivoHabilitado
        fields = [
            'uuid', 'nome_arquivo', 'arquivo', 'status', 'concurso_uuid', 'concurso_nome',
            'criado_em', 'atualizado_em', 'erros'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em', 'erros']

    def get_erros(self, obj):
        """Retorna os erros associados à importação, se existirem."""
        if ImportacaoArquivoHabilitadosListSerializer._content_type_cache is None:
            ImportacaoArquivoHabilitadosListSerializer._content_type_cache = ContentType.objects.get_for_model(ImportacaoArquivoHabilitado)
        
        erros_queryset = ImportacaoErro.objects.filter(
            content_type=ImportacaoArquivoHabilitadosListSerializer._content_type_cache,
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
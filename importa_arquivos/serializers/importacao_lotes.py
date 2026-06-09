"""Módulo serializers/importacao_lotes."""
from __future__ import annotations
from typing import Any
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from ..models import ImportacaoErro, ImportacaoLotes

class ImportacaoLotesCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de importações de lotes.

    Aceita arquivo TXT, concurso_uuid e concurso_nome.
    """

    class Meta:
        """Define Meta."""
        model = ImportacaoLotes
        fields = ['arquivo', 'concurso_uuid', 'concurso_nome']

    def create(self, validated_data: Any) -> Any:
        """Executa create."""
        arquivo = validated_data.get('arquivo')
        nome_arquivo = getattr(arquivo, 'name', None) or 'Importação de Lotes'
        instance = ImportacaoLotes.objects.create(nome_arquivo=nome_arquivo, tipo='LOTES', status='PENDENTE', **validated_data)
        return instance

class ImportacaoLotesListSerializer(serializers.ModelSerializer):
    """Serializer para listagem e detalhe de importações de lotes.

    Erros são consultados na tabela ImportacaoErro (GenericForeignKey).
    """
    erros = serializers.SerializerMethodField()
    _content_type_cache = None

    class Meta:
        """Define Meta."""
        model = ImportacaoLotes
        fields = ['uuid', 'nome_arquivo', 'arquivo', 'tipo', 'concurso_uuid', 'concurso_nome', 'status', 'total_atualizados', 'erros', 'detalhes', 'criado_em', 'atualizado_em']
        read_only_fields = ['uuid', 'tipo', 'criado_em', 'atualizado_em', 'status', 'total_atualizados', 'detalhes']

    def get_erros(self, obj: Any) -> Any:
        """Executa get erros."""
        if ImportacaoLotesListSerializer._content_type_cache is None:
            ImportacaoLotesListSerializer._content_type_cache = ContentType.objects.get_for_model(ImportacaoLotes)
        erros_qs = ImportacaoErro.objects.filter(content_type=ImportacaoLotesListSerializer._content_type_cache, object_id=obj.uuid).order_by('-criado_em')
        if not erros_qs.exists():
            return None
        return [{'mensagem': e.mensagem, 'erros': e.erros, 'criado_em': e.criado_em} for e in erros_qs]

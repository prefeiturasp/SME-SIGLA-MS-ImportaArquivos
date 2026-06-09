"""Módulo serializers/importacao_erros."""
from __future__ import annotations
from typing import Any
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from ..models import ImportacaoArquivoHabilitado, ImportacaoArquivoVagas, ImportacaoErro, ImportacaoEscolhas, ImportacaoLotes

class ImportacaoErrosListSerializer(serializers.Serializer):
    """Define ImportacaoErrosListSerializer."""
    concurso_uuid = serializers.UUIDField(required=False, allow_null=True)
    processo_uuid = serializers.UUIDField(required=False, allow_null=True)
    mensagem = serializers.CharField()
    erros = serializers.CharField()

    def to_representation(self, instance: ImportacaoErro) -> Any:
        """Executa to representation.
        
        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'mensagem': instance.mensagem, 'erros': instance.erros, 'concurso_uuid': None, 'processo_uuid': None}
        try:
            obj = instance.importacao_obj
            if obj is not None:
                if isinstance(obj, ImportacaoArquivoHabilitado):
                    data['concurso_uuid'] = obj.concurso_uuid  # type: ignore[assignment]
                elif isinstance(obj, ImportacaoArquivoVagas | ImportacaoEscolhas):
                    data['processo_uuid'] = obj.processo_uuid  # type: ignore[assignment]
                elif isinstance(obj, ImportacaoLotes):
                    data['concurso_uuid'] = obj.concurso_uuid  # type: ignore[assignment]
        except Exception:
            pass
        return data

def queryset_erros_por_modelo(model_cls: Any, importacao_uuid: Any=None) -> Any:
    """Executa queryset erros por modelo.
    
    Args:
        model_cls: Parâmetro model cls da operação.
        importacao_uuid: Parâmetro importacao uuid da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    content_type = ContentType.objects.get_for_model(model_cls)
    qs = ImportacaoErro.objects.filter(content_type=content_type)
    if importacao_uuid:
        qs = qs.filter(object_id=importacao_uuid)
    return qs

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from ..models import (
    ImportacaoErro,
    ImportacaoArquivoHabilitado,
    ImportacaoArquivoVagas,
    ImportacaoEscolhas,
    ImportacaoLotes,
)


class ImportacaoErrosListSerializer(serializers.Serializer):
    concurso_uuid = serializers.UUIDField(required=False, allow_null=True)
    processo_uuid = serializers.UUIDField(required=False, allow_null=True)
    mensagem = serializers.CharField()
    erros = serializers.CharField()

    def to_representation(self, instance: ImportacaoErro):
        data = {
            'mensagem': instance.mensagem,
            'erros': instance.erros,
            'concurso_uuid': None,
            'processo_uuid': None,
        }

        # Resolve objeto relacionado via GenericForeignKey
        try:
            obj = instance.importacao_obj
            if obj is not None:
                if isinstance(obj, ImportacaoArquivoHabilitado):
                    data['concurso_uuid'] = obj.concurso_uuid
                elif isinstance(obj, ImportacaoArquivoVagas):
                    data['processo_uuid'] = obj.processo_uuid
                elif isinstance(obj, ImportacaoEscolhas):
                    data['processo_uuid'] = obj.processo_uuid
                elif isinstance(obj, ImportacaoLotes):
                    data['concurso_uuid'] = obj.concurso_uuid
        except Exception:
            # Se o objeto foi deletado ou não existe, mantém None
            pass

        return data


def queryset_erros_por_modelo(model_cls, importacao_uuid=None):
    content_type = ContentType.objects.get_for_model(model_cls)
    qs = ImportacaoErro.objects.filter(content_type=content_type)
    if importacao_uuid:
        qs = qs.filter(object_id=importacao_uuid)
    return qs



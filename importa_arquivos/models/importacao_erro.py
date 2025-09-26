from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from .base import BaseModel


class ImportacaoErro(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    importacao_obj = GenericForeignKey('content_type', 'object_id')

    mensagem = models.CharField(max_length=255, verbose_name="Mensagem curta do erro")
    erros = models.TextField(verbose_name="Erros da importação")

    class Meta:
        db_table = 'importacao_erros'
        verbose_name = 'Erro de Importação'
        verbose_name_plural = 'Erros de Importação'
        ordering = ['-criado_em'] 
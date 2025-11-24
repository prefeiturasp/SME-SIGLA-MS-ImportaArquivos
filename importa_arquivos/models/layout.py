from random import choice
import uuid
from django.db import models
from django.utils import timezone
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from .base import BaseModel, CHOICES_TIPO_IMPORTACAO_ARQUIVO


class LayoutArquivoImportacao(BaseModel):
    """
    Model para layout de importação de arquivos.
    """
    history = AuditlogHistoryField()
    tipo = models.CharField(
        max_length=20,
        verbose_name="Tipo de arquivo",
        choices=CHOICES_TIPO_IMPORTACAO_ARQUIVO,
        default='HABILITADOS',
    )
    estrutura = models.JSONField(verbose_name="Estrutura do arquivo")

    class Meta:
        db_table = 'layout_arquivo_importacao'
        verbose_name = "Layout de importação de arquivo"
        verbose_name_plural = "Layouts de importação de arquivos"
        ordering = ['-criado_em']

    def __str__(self):
        return self.tipo


auditlog.register(LayoutArquivoImportacao)

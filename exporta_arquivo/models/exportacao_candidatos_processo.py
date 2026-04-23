import uuid
from django.db import models
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog

from .base import BaseModel


class ExportacaoCandidatosProcesso(BaseModel):
    """
    Registro de exportação de candidatos por processo.
    """
    history = AuditlogHistoryField()
    concurso_codigo = models.IntegerField(
        verbose_name="Código do concurso",
        null=True,
        blank=True,
    )
    concurso_data_criacao = models.DateTimeField(
        verbose_name="Data de criação do concurso",
        null=True,
        blank=True,    
    )    
   
    class Meta:
        db_table = 'exportacao_candidatos_processo'
        verbose_name = "Exportação de candidatos processo"
        verbose_name_plural = "Exportações de candidatos processo"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Exportação {self.uuid} (processo={self.processo_uuid}, cargo={self.cargo_uuid})"


auditlog.register(ExportacaoCandidatosProcesso)

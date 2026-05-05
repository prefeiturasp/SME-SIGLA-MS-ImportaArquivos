import uuid
from django.db import models
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog

from .base import BaseModel


class ExportacaoVagasProcesso(BaseModel):
    """
    Registro de exportação de vagas por processo (formato vagas processo).
    """
    history = AuditlogHistoryField()

    class Meta:
        db_table = 'exportacao_vagas_processo'
        verbose_name = "Exportação de vagas processo"
        verbose_name_plural = "Exportações de vagas processo"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Exportação {self.uuid} (processo={self.processo_uuid}, cargo={self.cargo_uuid})"


auditlog.register(ExportacaoVagasProcesso)

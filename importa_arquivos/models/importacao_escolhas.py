from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models

from .base import CHOICES_STATUS_IMPORTACAO_ARQUIVO, BaseModel


class ImportacaoEscolhas(BaseModel):
    """
    Model para importação de escolhas da API externa.
    """

    history = AuditlogHistoryField()
    processo_uuid = models.UUIDField(
        verbose_name="UUID do processo de convocação", null=True, blank=True
    )
    processo_id = models.IntegerField(
        verbose_name="ID do processo", null=True, blank=True
    )
    concurso_uuid = models.UUIDField(
        verbose_name="UUID do concurso", null=True, blank=True
    )
    dados_prodam = models.JSONField(
        verbose_name="Dados da importação da API PRODAM", null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=CHOICES_STATUS_IMPORTACAO_ARQUIVO,
        default=CHOICES_STATUS_IMPORTACAO_ARQUIVO[2][0],  # CONCLUIDO
        verbose_name="Status",
    )

    class Meta:
        db_table = "importacao_escolhas"
        verbose_name = "Importação de escolhas"
        verbose_name_plural = "Importações de escolhas"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Importação - {self.processo_uuid or 'N/A'}"


auditlog.register(ImportacaoEscolhas)

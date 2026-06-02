from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog

from .base import BaseModel


class ExportacaoVagasSigpec(BaseModel):
    """
    Registro de exportação de vagas em formato SIGPEC.
    """

    history = AuditlogHistoryField()

    class Meta:
        db_table = "exportacao_vagas_sigpec"
        verbose_name = "Exportação de vagas SIGPEC"
        verbose_name_plural = "Exportações de vagas SIGPEC"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Exportação {self.uuid} (processo={self.processo_uuid}, cargo={self.cargo_uuid})"  # noqa: E501


auditlog.register(ExportacaoVagasSigpec)

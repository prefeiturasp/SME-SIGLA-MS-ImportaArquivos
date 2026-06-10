"""Módulo models/exportacao_vagas_processo."""

from __future__ import annotations

from typing import Any

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog

from .base import BaseModel


class ExportacaoVagasProcesso(BaseModel):
    """Registro de exportação de vagas por processo (formato vagas processo)."""

    history = AuditlogHistoryField()

    class Meta:
        """Representa Meta."""

        db_table = "exportacao_vagas_processo"
        verbose_name = "Exportação de vagas processo"
        verbose_name_plural = "Exportações de vagas processo"
        ordering = ["-criado_em"]

    def __str__(self) -> Any:
        """Retorna representação textual do registro.

        Args:
            self: Instância do objeto.

        Returns:
            Valor calculado conforme a regra aplicada.
        """
        return f"Exportação {self.uuid} (processo={self.processo_uuid}, cargo={self.cargo_uuid})"


auditlog.register(ExportacaoVagasProcesso)

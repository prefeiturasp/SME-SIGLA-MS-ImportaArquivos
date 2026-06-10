"""Módulo models/exportacao_candidatos_processo."""

from __future__ import annotations

from typing import Any

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models

from .base import BaseModel


class ExportacaoCandidatosProcesso(BaseModel):
    """Registro de exportação de candidatos por processo."""

    history = AuditlogHistoryField()
    concurso_codigo = models.IntegerField(
        verbose_name="Código do concurso", null=True, blank=True
    )
    concurso_data_criacao = models.DateTimeField(
        verbose_name="Data de criação do concurso", null=True, blank=True
    )

    class Meta:
        """Representa Meta."""

        db_table = "exportacao_candidatos_processo"
        verbose_name = "Exportação de candidatos processo"
        verbose_name_plural = "Exportações de candidatos processo"
        ordering = ["-criado_em"]

    def __str__(self) -> Any:
        """Retorna representação textual do registro.

        Args:
            self: Instância do objeto.

        Returns:
            Valor calculado conforme a regra aplicada.
        """
        return f"Exportação {self.uuid} (processo={self.processo_uuid}, cargo={self.cargo_uuid})"


auditlog.register(ExportacaoCandidatosProcesso)

"""Módulo models/exportacao_lote."""

from __future__ import annotations

from typing import Any

from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models

from core.models import BaseModel


class StatusExportacao(models.TextChoices):
    """Representa StatusExportacao."""

    PENDENTE = ("PENDENTE", "Pendente")
    PROCESSANDO = ("PROCESSANDO", "Processando")
    SUCESSO = ("SUCESSO", "Sucesso")
    ATENCAO = ("ATENCAO", "Atenção")
    ERRO = ("ERRO", "Erro")


class ExportacaoLote(BaseModel):
    """Histórico de exportações de lotes (SIGPEC/ERGON)."""

    history = AuditlogHistoryField()
    status = models.CharField(
        max_length=20,
        choices=StatusExportacao.choices,
        default=StatusExportacao.SUCESSO,
        verbose_name="Status da Exportação",
    )
    concurso_uuid = models.UUIDField(verbose_name="UUID do Concurso")
    concurso_nome = models.CharField(
        max_length=255, verbose_name="Nome do Concurso"
    )
    lote_uuid = models.UUIDField(verbose_name="UUID do Lote")
    numero_lote = models.IntegerField(verbose_name="Número do Lote")
    codigo_cargo = models.CharField(
        max_length=20, verbose_name="Código do Cargo", null=True, blank=True
    )
    conteudo_arquivo = models.TextField(
        verbose_name="Conteúdo do arquivo exportado", null=True, blank=True
    )
    nome_arquivo = models.CharField(
        max_length=255,
        verbose_name="Nome do arquivo exportado",
        null=True,
        blank=True,
    )

    class Meta:
        """Representa Meta."""

        db_table = "exportacao_lote"
        verbose_name = "Exportação de Lote"
        verbose_name_plural = "Exportações de Lote"
        ordering = ["-criado_em"]

    def __str__(self) -> Any:
        """Retorna UUID, concurso e lote da exportação."""
        return (
            f"Exportação Lote {self.uuid} "
            f"(concurso={self.concurso_uuid}, lote={self.lote_uuid})"
        )


auditlog.register(ExportacaoLote)

"""Módulo models/importacao_lotes."""
from __future__ import annotations
from typing import Any
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models
from .base import BaseModelArquivoImportacao

class ImportacaoLotes(BaseModelArquivoImportacao):
    """Registro de importação de arquivo de lotes de classificação (SIGPEC)."""
    history = AuditlogHistoryField()
    concurso_uuid = models.UUIDField(verbose_name='UUID do Concurso')
    concurso_nome = models.CharField(max_length=255, null=True, blank=True, verbose_name='Nome do Concurso')
    total_atualizados = models.IntegerField(null=True, blank=True, verbose_name='Total de Candidatos Atualizados')
    detalhes = models.JSONField(null=True, blank=True, verbose_name='Detalhes da Atualização')

    class Meta:
        """Define Meta."""
        db_table = 'importacao_lotes'
        verbose_name = 'Importação de Lotes'
        verbose_name_plural = 'Importações de Lotes'
        ordering = ['-criado_em']

    def __str__(self) -> Any:
        """Executa   str  ."""
        return self.nome_arquivo
auditlog.register(ImportacaoLotes)

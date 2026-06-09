"""Módulo models/importacao_habilitados."""
from __future__ import annotations
from typing import Any
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models
from .base import BaseModelArquivoImportacao

class ImportacaoArquivoHabilitado(BaseModelArquivoImportacao):
    """Model para importação de arquivos de candidatos habilitados."""
    history = AuditlogHistoryField()
    concurso_uuid = models.UUIDField(verbose_name='UUID do concurso')
    concurso_nome = models.CharField(max_length=255, verbose_name='Nome do concurso', null=True, blank=True)

    class Meta:
        """Define Meta."""
        db_table = 'importacao_arquivo_habilitado'
        verbose_name = 'Importação de arquivo habilitado'
        verbose_name_plural = 'Importações de arquivos habilitados'
        ordering = ['-criado_em']

    def __str__(self) -> Any:
        """Executa   str  ."""
        return self.nome_arquivo
auditlog.register(ImportacaoArquivoHabilitado)

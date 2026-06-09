"""Módulo models/importacao_vagas."""
from __future__ import annotations
from typing import Any
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models
from .base import BaseModelArquivoImportacao

class ImportacaoArquivoVagas(BaseModelArquivoImportacao):
    """Model para importação de arquivos de vagas."""
    history = AuditlogHistoryField()
    processo_uuid = models.UUIDField(verbose_name='UUID do processo de convocação', null=True, blank=True)
    processo_nome = models.CharField(max_length=255, verbose_name='Nome do processo de convocação', null=True, blank=True)

    class Meta:
        """Define Meta."""
        db_table = 'importacao_arquivo_vagas'
        verbose_name = 'Importação de arquivo de vagas'
        verbose_name_plural = 'Importações de arquivos de vagas'
        ordering = ['-criado_em']

    def __str__(self) -> Any:
        """Executa   str  .
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return self.nome_arquivo
auditlog.register(ImportacaoArquivoVagas)

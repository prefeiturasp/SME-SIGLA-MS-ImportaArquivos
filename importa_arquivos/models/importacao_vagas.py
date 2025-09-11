import uuid
from django.db import models
from django.utils import timezone
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from .base import BaseModelArquivoImportacao


class ImportacaoArquivoVagas(BaseModelArquivoImportacao):
    """
    Model para importação de arquivos de vagas.
    """
    history = AuditlogHistoryField()

    class Meta:
        db_table = 'importacao_arquivo_vagas'
        verbose_name = "Importação de arquivo de vagas"
        verbose_name_plural = "Importações de arquivos de vagas"
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_arquivo


auditlog.register(ImportacaoArquivoVagas)

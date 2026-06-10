from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models

from .base import BaseModelArquivoImportacao


class ImportacaoArquivoVagas(BaseModelArquivoImportacao):
    """
    Model para importação de arquivos de vagas.
    """

    history = AuditlogHistoryField()
    processo_uuid = models.UUIDField(
        verbose_name="UUID do processo de convocação", null=True, blank=True
    )
    concurso_uuid = models.UUIDField(
        verbose_name="UUID do concurso", null=True, blank=True
    )
    processo_nome = models.CharField(
        max_length=255,
        verbose_name="Nome do processo de convocação",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "importacao_arquivo_vagas"
        verbose_name = "Importação de arquivo de vagas"
        verbose_name_plural = "Importações de arquivos de vagas"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.nome_arquivo


auditlog.register(ImportacaoArquivoVagas)

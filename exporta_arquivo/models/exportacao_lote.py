import uuid
from django.db import models


class ExportacaoLote(models.Model):
    """
    Histórico de exportações de lotes (SIGPEC/ERGON).
    """
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    concurso_uuid = models.UUIDField(verbose_name="UUID do Concurso")
    concurso_nome = models.CharField(
        max_length=255,
        verbose_name="Nome do Concurso",
        null=True,
        blank=True,
    )
    lote_uuid = models.UUIDField(verbose_name="UUID do Lote")
    conteudo_arquivo = models.TextField(
        verbose_name="Conteúdo do arquivo exportado",
        null=True,
        blank=True,
    )
    nome_arquivo = models.CharField(
        max_length=255,
        verbose_name="Nome do arquivo exportado",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "exportacao_lote"
        verbose_name = "Exportação de Lote"
        verbose_name_plural = "Exportações de Lote"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Exportação Lote {self.uuid} (concurso={self.concurso_uuid}, lote={self.lote_uuid})"

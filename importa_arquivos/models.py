import uuid
from django.db import models
from django.utils import timezone
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog


class BaseModel(models.Model):
    """
    Model base com UUID, criado_em e atualizado_em.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        abstract = True


 


class ImportacaoArquivos(BaseModel):
    """
    Model para importação de arquivos.
    """
    history = AuditlogHistoryField()
    nome = models.CharField(max_length=200, verbose_name="Nome do Arquivo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    arquivo = models.FileField(upload_to='importacoes/', verbose_name="Arquivo")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('processando', 'Processando'),
            ('concluido', 'Concluído'),
            ('erro', 'Erro'),
        ],
        default='pendente',
        verbose_name="Status"
    )

    class Meta:
        db_table = 'importacao_arquivos'
        verbose_name = "Importação de Arquivo"
        verbose_name_plural = "Importações de Arquivos"
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome


auditlog.register(ImportacaoArquivos)

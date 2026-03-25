from django.db import models
from .base import BaseModel


CHOICES_STATUS_IMPORTACAO_LOTES = [
    ('PENDENTE', 'Pendente'),
    ('CONCLUIDO', 'Concluído'),
    ('ERRO', 'Erro'),
]


class ImportacaoLotes(BaseModel):
    """
    Registro de importação de arquivo de lotes de classificação (SIGPEC).
    """
    nome_arquivo = models.CharField(max_length=200, verbose_name="Nome do Arquivo")
    arquivo = models.FileField(upload_to='importacoes_lotes/', verbose_name="Arquivo")
    concurso_uuid = models.UUIDField(verbose_name="UUID do Concurso")
    concurso_nome = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nome do Concurso")
    status = models.CharField(
        max_length=20,
        choices=CHOICES_STATUS_IMPORTACAO_LOTES,
        default='PENDENTE',
        verbose_name="Status",
    )
    total_atualizados = models.IntegerField(null=True, blank=True, verbose_name="Total de Candidatos Atualizados")
    erros = models.TextField(null=True, blank=True, verbose_name="Erros")
    detalhes = models.JSONField(null=True, blank=True, verbose_name="Detalhes da Atualização")

    class Meta:
        db_table = 'importacao_lotes'
        verbose_name = 'Importação de Lotes'
        verbose_name_plural = 'Importações de Lotes'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_arquivo

from django.db import models
from .base import BaseModel


class ExportacaoVagasSigpec(BaseModel):
    """
    Registro de exportação de vagas em formato SIGPEC.
    """
    processo_uuid = models.UUIDField(verbose_name="UUID do processo de convocação")
    cargo_uuid = models.UUIDField(verbose_name="UUID do cargo")
    concurso_uuid = models.UUIDField(
        verbose_name="UUID do concurso",
        null=True,
        blank=True,
    )
    concurso_nome = models.CharField(
        max_length=255,
        verbose_name="Nome do concurso",
        null=True,
        blank=True,
    )
    processo_nome = models.CharField(
        max_length=500,
        verbose_name="Nome do processo",
        null=True,
        blank=True,
    )
    cargo_nome = models.CharField(
        max_length=255,
        verbose_name="Nome do cargo",
        null=True,
        blank=True,
    )
    cargo_codigo = models.IntegerField(
        verbose_name="Código do cargo (integração)",
        null=True,
        blank=True,
    )
    conteudo_arquivo = models.TextField(
        verbose_name="Conteúdo do arquivo exportado",
        null=True,
        blank=True,
    )
    nome_arquivo = models.CharField(
        max_length=255,
        verbose_name="Nome do arquivo na exportação",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'exportacao_vagas_sigpec'
        verbose_name = "Exportação de vagas SIGPEC"
        verbose_name_plural = "Exportações de vagas SIGPEC"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Exportação {self.uuid} (processo={self.processo_uuid}, cargo={self.cargo_uuid})"

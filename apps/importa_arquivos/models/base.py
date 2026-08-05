"""Módulo models/base."""

from django.db import models

from core.models import BaseModel

CHOICES_TIPO_IMPORTACAO_ARQUIVO = [
    ("HABILITADOS", "Habilitados"),
    ("VAGAS", "Vagas"),
    ("LOTES", "Lotes"),
]


CHOICES_STATUS_IMPORTACAO_ARQUIVO = [
    ("PENDENTE", "Pendente"),
    ("PROCESSANDO", "Processando"),
    ("CONCLUIDO", "Concluído"),
    ("ERRO", "Erro"),
]


class BaseModelArquivoImportacao(BaseModel):
    """Model base com nome do arquivo, arquivo e status."""

    nome_arquivo = models.CharField(
        max_length=200, verbose_name="Nome do Arquivo"
    )
    arquivo = models.FileField(
        upload_to="importacoes/", verbose_name="Arquivo"
    )
    tipo = models.CharField(
        max_length=20,
        choices=CHOICES_TIPO_IMPORTACAO_ARQUIVO,
    )
    status = models.CharField(
        max_length=20,
        choices=CHOICES_STATUS_IMPORTACAO_ARQUIVO,
        default=CHOICES_STATUS_IMPORTACAO_ARQUIVO[0][0],
        verbose_name="Status",
    )

    class Meta:
        """Representa Meta."""

        abstract = True

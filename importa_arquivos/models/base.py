"""Módulo models/base."""

import uuid

from django.db import models

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


class BaseModel(models.Model):
    """Model base com UUID, criado_em e atualizado_em."""

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    criado_em = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Criação"
    )
    atualizado_em = models.DateTimeField(
        auto_now=True, verbose_name="Data de Atualização"
    )

    class Meta:
        """Define Meta."""

        abstract = True


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
        """Define Meta."""

        abstract = True

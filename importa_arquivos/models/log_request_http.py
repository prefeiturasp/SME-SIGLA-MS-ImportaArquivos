"""Módulo models/log_request_http."""

from __future__ import annotations

from typing import Any

from django.db import models

from .base import BaseModel


class LogRequestHttp(BaseModel):
    """Model para log de requisições HTTP."""

    url = models.URLField(max_length=500, verbose_name="URL chamada")
    metodo_http = models.CharField(max_length=10, verbose_name="Método HTTP")
    processo_id = models.IntegerField(
        verbose_name="ID do processo", null=True, blank=True
    )
    resposta_raw = models.TextField(
        verbose_name="Resposta raw (sem formatação)"
    )

    class Meta:
        """Representa Meta."""

        db_table = "log_request_http"
        verbose_name = "Log de requisição HTTP"
        verbose_name_plural = "Log de requisição HTTP"
        ordering = ["-criado_em"]

    def __str__(self) -> Any:
        """Retorna representação textual do registro.

        Args:
            self: Instância do objeto.

        Returns:
            Valor calculado conforme a regra aplicada.
        """
        return f'Log - {self.metodo_http} {self.url} - Processo: {self.processo_id or 'N/A'}'  # noqa: E501

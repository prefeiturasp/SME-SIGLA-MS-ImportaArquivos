from django.db import models
from .base import BaseModel


class LogRequestHttp(BaseModel):
    """
    Model para log de requisições HTTP.
    Armazena informações brutas das requisições e respostas.
    """
    url = models.URLField(max_length=500, verbose_name="URL chamada")
    metodo_http = models.CharField(max_length=10, verbose_name="Método HTTP")
    processo_id = models.IntegerField(verbose_name="ID do processo", null=True, blank=True)
    resposta_raw = models.TextField(verbose_name="Resposta raw (sem formatação)")

    class Meta:
        db_table = 'log_request_http'
        verbose_name = "Log de requisição HTTP"
        verbose_name_plural = "Log de requisição HTTP"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Log - {self.metodo_http} {self.url} - Processo: {self.processo_id or 'N/A'}"


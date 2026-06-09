"""Módulo models/cabecalho_exportacao_lote."""
from __future__ import annotations
from typing import Any
import uuid
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models

class CabecalhoExportacaoLote(models.Model):
    """Cabeçalho configurável para o arquivo de exportação de lotes.

    Cada linha @-prefixada do arquivo é um campo editável.
    """
    history = AuditlogHistoryField()
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    tabela = models.CharField(max_length=500, verbose_name='@TABELA', default='[c_ERGON][PMSP_ESCOLHA_VAGA_SME][1.0]')
    chave = models.CharField(max_length=500, verbose_name='@CHAVE', default='[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER]')
    tag_inicio = models.CharField(max_length=255, verbose_name='@TAG INICIO', blank=True, default='')
    tag_fim = models.CharField(max_length=255, verbose_name='@TAG FIM', blank=True, default='')
    separador = models.CharField(max_length=10, verbose_name='@SEPARADOR', default=';')
    formato_data = models.CharField(max_length=50, verbose_name='@FORMATO DATA', default='DD/MM/YYYY')
    colunas = models.CharField(max_length=1000, verbose_name='@COLUNAS', default='[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER][DATA_ESCOLHA][DATE][ESCOLHEU_VAGA][VARCHAR2][SETOR][VARCHAR2]')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        """Define Meta."""
        db_table = 'cabecalho_exportacao_lote'
        verbose_name = 'Cabeçalho de Exportação de Lote'
        verbose_name_plural = 'Cabeçalhos de Exportação de Lote'
        ordering = ['-criado_em']

    def __str__(self) -> Any:
        """Executa   str  ."""
        return f'Cabeçalho {self.uuid} ({('ativo' if self.ativo else 'inativo')})'

    def render(self) -> str:
        """Gera o bloco de cabeçalho completo para o arquivo exportado."""
        sep = self.separador
        return f'@TABELA={self.tabela}\n@CHAVE={self.chave}\n@TAG INICIO={self.tag_inicio}\n@TAG FIM={self.tag_fim}\n@SEPARADOR={sep}\n@FORMATO DATA={self.formato_data}\n@COLUNAS={self.colunas}\n'
auditlog.register(CabecalhoExportacaoLote)

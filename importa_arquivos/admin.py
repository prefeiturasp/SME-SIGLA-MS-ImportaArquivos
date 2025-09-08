"""
Django admin configuration for the importa_arquivos module.
"""
from django.contrib import admin
from django.forms import JSONField
from django.contrib.admin.widgets import AdminTextareaWidget
from .models import ImportacaoArquivos


@admin.register(ImportacaoArquivos)
class ImportacaoArquivosAdmin(admin.ModelAdmin):
    """
    Admin para o modelo ImportacaoArquivos.
    """
    list_display = ['concurso', 'cargo', 'arquivo_nome_original', 'arquivo_tamanho_mb', 'tipo_de_layout', 'status', 'criado_em']
    list_filter = ['tipo_de_layout', 'status', 'arquivo_content_type', 'criado_em', 'atualizado_em']
    search_fields = ['concurso', 'cargo', 'arquivo_nome_original']
    readonly_fields = ['uuid', 'arquivo_nome_original', 'arquivo_tamanho', 'arquivo_content_type', 'status', 'criado_em', 'atualizado_em']
    ordering = ['-criado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('concurso', 'cargo', 'tipo_de_layout')
        }),
        ('Informações do Arquivo', {
            'fields': ('arquivo_nome_original', 'arquivo_tamanho', 'arquivo_content_type'),
            'classes': ('collapse',)
        }),
        ('Status e Metadados', {
            'fields': ('status', 'uuid', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def arquivo_tamanho_mb(self, obj):
        if obj.arquivo_tamanho:
            return f"{obj.arquivo_tamanho / 1024 / 1024:.2f} MB"
        return "0 MB"
    arquivo_tamanho_mb.short_description = 'Tamanho'




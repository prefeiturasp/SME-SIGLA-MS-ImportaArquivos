"""
Django admin configuration for the importa_arquivos module.
"""
from django.contrib import admin
from .models import ImportacaoArquivos


@admin.register(ImportacaoArquivos)
class ImportacaoArquivosAdmin(admin.ModelAdmin):
    """
    Admin para o modelo ImportacaoArquivos.
    """
    list_display = ['nome', 'status', 'uuid', 'criado_em', 'atualizado_em']
    list_filter = ['status', 'criado_em', 'atualizado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['uuid', 'criado_em', 'atualizado_em']
    ordering = ['-criado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'arquivo', 'status')
        }),
        ('Metadados', {
            'fields': ('uuid', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


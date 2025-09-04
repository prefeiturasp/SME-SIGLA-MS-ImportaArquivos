"""
Django admin configuration for the importa_arquivos module.
"""
from django.contrib import admin
from django.forms import JSONField
from django.contrib.admin.widgets import AdminTextareaWidget
from .models import ImportacaoArquivos, Layout


@admin.register(ImportacaoArquivos)
class ImportacaoArquivosAdmin(admin.ModelAdmin):
    """
    Admin para o modelo ImportacaoArquivos.
    """
    list_display = ['nome', 'tipo_de_layout', 'status', 'uuid', 'criado_em', 'atualizado_em']
    list_filter = ['tipo_de_layout', 'status', 'criado_em', 'atualizado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['uuid', 'criado_em', 'atualizado_em']
    ordering = ['-criado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'arquivo', 'tipo_de_layout', 'status')
        }),
        ('Metadados', {
            'fields': ('uuid', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Layout)
class LayoutAdmin(admin.ModelAdmin):
    """
    Admin para o modelo Layout.
    """
    list_display = ['tipo_de_layout', 'total_campos', 'uuid', 'criado_em', 'atualizado_em']
    list_filter = ['tipo_de_layout', 'criado_em', 'atualizado_em']
    search_fields = ['tipo_de_layout']
    readonly_fields = ['uuid', 'criado_em', 'atualizado_em', 'total_campos']
    ordering = ['-criado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo_de_layout', 'dados')
        }),
        ('Metadados', {
            'fields': ('uuid', 'total_campos', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    # Customizar widget para o campo JSON
    formfield_overrides = {
        JSONField: {'widget': AdminTextareaWidget(attrs={'rows': 15, 'cols': 80})},
    }
    
    def total_campos(self, obj):
        """
        Mostra o total de campos no layout.
        """
        return obj.total_campos
    
    total_campos.short_description = 'Total de Campos'


from django.contrib import admin
from .models import ImportacaoArquivoHabilitado, LayoutArquivoImportacao


@admin.register(LayoutArquivoImportacao)
class LayoutArquivoImportacaoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'criado_em', 'atualizado_em')
    search_fields = ('tipo',)
    list_filter = ('tipo',)
    ordering = ('-criado_em',)
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')


@admin.register(ImportacaoArquivoHabilitado)
class ImportacaoArquivoHabilitadoAdmin(admin.ModelAdmin):
    list_display = ('nome_arquivo', 'concurso_uuid', 'concurso_nome', 'status', 'criado_em')
    search_fields = ('nome_arquivo', 'concurso_uuid', 'concurso_nome')
    list_filter = ('status',)
    ordering = ('-criado_em',)
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')

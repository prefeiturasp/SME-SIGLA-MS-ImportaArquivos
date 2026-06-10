"""Módulo admin."""

from django.contrib import admin

from .models import (
    ImportacaoArquivoHabilitado,
    ImportacaoArquivoVagas,
    ImportacaoErro,
    LayoutArquivoImportacao,
)


@admin.register(LayoutArquivoImportacao)
class LayoutArquivoImportacaoAdmin(admin.ModelAdmin):
    """Configuração do admin para LayoutArquivoImportacao."""

    list_display = ("tipo", "criado_em", "atualizado_em")
    search_fields = ("tipo",)
    list_filter = ("tipo",)
    ordering = ("-criado_em",)
    readonly_fields = ("uuid", "criado_em", "atualizado_em")


@admin.register(ImportacaoArquivoHabilitado)
class ImportacaoArquivoHabilitadoAdmin(admin.ModelAdmin):
    """Configuração do admin para ImportacaoArquivoHabilitado."""

    list_display = (
        "nome_arquivo",
        "concurso_uuid",
        "concurso_nome",
        "status",
        "criado_em",
    )
    search_fields = ("nome_arquivo", "concurso_uuid", "concurso_nome")
    list_filter = ("status",)
    ordering = ("-criado_em",)
    readonly_fields = ("uuid", "criado_em", "atualizado_em")


@admin.register(ImportacaoArquivoVagas)
class ImportacaoArquivoVagasAdmin(admin.ModelAdmin):
    """Configuração do admin para ImportacaoArquivoVagas."""

    list_display = ("nome_arquivo", "status", "criado_em")
    search_fields = ("nome_arquivo",)
    list_filter = ("status",)
    ordering = ("-criado_em",)
    readonly_fields = ("uuid", "criado_em", "atualizado_em")


@admin.register(ImportacaoErro)
class ImportacaoErroAdmin(admin.ModelAdmin):
    """Configuração do admin para ImportacaoErro."""

    list_display = ("mensagem", "content_type", "object_id", "criado_em")
    search_fields = ("mensagem", "erros")
    list_filter = ("content_type",)
    ordering = ("-criado_em",)
    readonly_fields = ("uuid", "criado_em", "atualizado_em")

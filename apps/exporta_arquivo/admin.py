"""Módulo admin."""

from django.contrib import admin

from .models import ExportacaoVagasProcesso, ExportacaoVagasSigpec


@admin.register(ExportacaoVagasSigpec)
class ExportacaoVagasSigpecAdmin(admin.ModelAdmin):
    """Configuração do admin para ExportacaoVagasSigpec."""

    list_display = (
        "uuid",
        "processo_uuid",
        "cargo_uuid",
        "concurso_uuid",
        "concurso_nome",
        "criado_em",
    )
    list_filter = ("criado_em",)
    search_fields = ("concurso_nome",)
    readonly_fields = ("uuid", "criado_em", "atualizado_em")


@admin.register(ExportacaoVagasProcesso)
class ExportacaoVagasProcessoAdmin(admin.ModelAdmin):
    """Configuração do admin para ExportacaoVagasProcesso."""

    list_display = (
        "uuid",
        "processo_uuid",
        "cargo_uuid",
        "concurso_uuid",
        "concurso_nome",
        "criado_em",
    )
    list_filter = ("criado_em",)
    search_fields = ("concurso_nome",)
    readonly_fields = ("uuid", "criado_em", "atualizado_em")

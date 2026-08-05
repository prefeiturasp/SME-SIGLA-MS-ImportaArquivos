"""Módulo apps."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """App core com recursos compartilhados entre os demais apps."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

"""Módulo apps."""

from django.apps import AppConfig


class ImportaArquivosConfig(AppConfig):
    """Representa ImportaArquivosConfig."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "importa_arquivos"

    def ready(self) -> None:
        """Importa o Celery na inicialização do Django."""
        try:  # noqa: SIM105
            from config import celery_app  # noqa: F401
        except Exception:
            pass

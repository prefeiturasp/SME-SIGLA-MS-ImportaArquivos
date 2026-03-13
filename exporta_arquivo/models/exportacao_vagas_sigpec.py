from django.db import models
from .base import BaseModel


class ExportacaoVagasSigpec(BaseModel):
    """
    Registro de exportação de vagas em formato SIGPEC.
    """   

    class Meta:
        db_table = 'exportacao_vagas_sigpec'
        verbose_name = "Exportação de vagas SIGPEC"
        verbose_name_plural = "Exportações de vagas SIGPEC"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Exportação {self.uuid} (processo={self.processo_uuid}, cargo={self.cargo_uuid})"

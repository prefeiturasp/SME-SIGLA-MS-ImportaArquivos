"""Módulo services/schema."""

from pydantic import BaseModel, field_validator

COLUNAS_ESPERADAS = {
    "LOTE",
    "EMPRESA",
    "VAGA",
    "IDENTIFICACAO",
    "CHAVE_INSCRITO",
    "NUMFUNC",
    "NUMVINC",
}


class LinhaLoteSIGPEC(BaseModel):
    """Schema de validação de uma linha do arquivo TXT de lotes SIGPEC."""

    lote: int
    empresa: str
    vaga: str
    identificacao: int
    chave_inscrito: str = ""  # opcional — ignorado na integração
    numfunc: int
    numvinc: int | None = None  # opcional

    @field_validator("empresa", "vaga", mode="before")
    @classmethod
    def nao_vazio(cls, v: str) -> str:
        """Valida se o campo não está vazio."""
        if not v or not str(v).strip():
            raise ValueError("Campo não pode estar vazio.")
        return str(v).strip()

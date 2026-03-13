"""Exceções do módulo de exportação."""


class BaseExportacaoException(Exception):
    def __init__(self, mensagem: str, detalhes: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.detalhes = detalhes or ''

    def __str__(self) -> str:
        return self.mensagem


class ExportacaoNotFoundException(BaseExportacaoException):
    """Processo ou cargo não encontrado (404)."""
    pass


class ExportacaoServiceUnavailableException(BaseExportacaoException):
    """API de convocação ou escolha indisponível ou retornando erro (502/503)."""
    pass


class ExportacaoBadRequestException(BaseExportacaoException):
    """Parâmetro obrigatório ausente ou inválido (400)."""
    pass

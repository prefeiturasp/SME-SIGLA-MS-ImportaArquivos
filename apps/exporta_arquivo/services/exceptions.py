"""Exceções do módulo de exportação."""

from __future__ import annotations


class BaseExportacaoError(Exception):
    """Erro de negócio relacionado a BaseExportacaoError."""

    def __init__(self, mensagem: str, detalhes: str | None = None) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            mensagem: Mensagem principal do erro.
            detalhes: Detalhes complementares do erro.
        """
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.detalhes = detalhes or ""

    def __str__(self) -> str:
        """Retorna a mensagem principal do erro."""
        return self.mensagem


class ExportacaoNotFoundError(BaseExportacaoError):
    """Processo ou cargo não encontrado (404)."""

    pass


class ExportacaoServiceUnavailableError(BaseExportacaoError):
    """API de convocação ou escolha indisponível ou retornando erro."""

    pass


class CandidatosNotFoundError(ExportacaoNotFoundError):
    """Recurso de candidatos não encontrado (404)."""

    pass


class CandidatosServiceUnavailableError(ExportacaoServiceUnavailableError):
    """API de candidatos indisponível ou retornando erro (502/503)."""

    pass


class EscolhasServiceUnavailableError(ExportacaoServiceUnavailableError):
    """API de escolhas indisponível ou retornando erro (502/503)."""

    pass


class ExportacaoBadRequestError(BaseExportacaoError):
    """Parâmetro obrigatório ausente ou inválido (400)."""

    pass


class ExportacaoLoteVazioError(BaseExportacaoError):
    """Lote sem candidatos cadastrados."""

    pass


class ExportacaoLoteIncompletaError(BaseExportacaoError):
    """Candidatos do lote sem escolha realizada."""

    def __init__(
        self,
        candidatos_sem_escolha: list[str],
        mensagem: str | None = None,
        detalhes: str | None = None,
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            candidatos_sem_escolha: Candidatos sem escolha registrada.
            mensagem: Mensagem principal do erro.
            detalhes: Detalhes complementares do erro.
        """
        self.candidatos_sem_escolha = candidatos_sem_escolha
        qtd = len(candidatos_sem_escolha)
        msg = mensagem or f"{qtd} candidato(s) sem escolha no lote."
        super().__init__(mensagem=msg, detalhes=detalhes or "")

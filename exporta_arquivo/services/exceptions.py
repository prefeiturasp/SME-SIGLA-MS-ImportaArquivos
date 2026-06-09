"""Exceções do módulo de exportação."""

from __future__ import annotations


class BaseExportacaoException(Exception):
    """Define BaseExportacaoException."""

    def __init__(self, mensagem: str, detalhes: str | None = None) -> None:
        """Executa   init  .

        Args:
            self: Instância do objeto.
            mensagem: Parâmetro mensagem.
            detalhes: Parâmetro detalhes.

        Raises:
            Nenhuma exceção específica documentada.
        """
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.detalhes = detalhes or ""

    def __str__(self) -> str:
        """Executa   str  .

        Args:
            self: Instância do objeto.

        Returns:
            Texto resultante da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return self.mensagem


class ExportacaoNotFoundException(BaseExportacaoException):
    """Processo ou cargo não encontrado (404)."""

    pass


class ExportacaoServiceUnavailableException(BaseExportacaoException):
    """API de convocação ou escolha indisponível ou retornando erro."""

    pass


class CandidatosNotFoundException(ExportacaoNotFoundException):
    """Recurso de candidatos não encontrado (404)."""

    pass


class CandidatosServiceUnavailableException(
    ExportacaoServiceUnavailableException
):
    """API de candidatos indisponível ou retornando erro (502/503)."""

    pass


class EscolhasServiceUnavailableException(
    ExportacaoServiceUnavailableException
):
    """API de escolhas indisponível ou retornando erro (502/503)."""

    pass


class ExportacaoBadRequestException(BaseExportacaoException):
    """Parâmetro obrigatório ausente ou inválido (400)."""

    pass


class ExportacaoLoteVazioException(BaseExportacaoException):
    """Lote sem candidatos cadastrados."""

    pass


class ExportacaoLoteIncompletaException(BaseExportacaoException):
    """Candidatos do lote sem escolha realizada."""

    def __init__(
        self,
        candidatos_sem_escolha: list[str],
        mensagem: str | None = None,
        detalhes: str | None = None,
    ) -> None:
        """Executa   init  .

        Args:
            self: Instância do objeto.
            candidatos_sem_escolha: Parâmetro candidatos sem escolha.
            mensagem: Parâmetro mensagem.
            detalhes: Parâmetro detalhes.

        Raises:
            Nenhuma exceção específica documentada.
        """
        self.candidatos_sem_escolha = candidatos_sem_escolha
        msg = (
            mensagem
            or f"{len(candidatos_sem_escolha)} candidato(s) sem escolha no lote."  # noqa: E501
        )
        super().__init__(mensagem=msg, detalhes=detalhes or "")

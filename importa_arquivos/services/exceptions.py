"""Módulo services/exceptions."""

from __future__ import annotations


class BaseImportacaoException(Exception):
    """Define BaseImportacaoException."""

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


class ColunaCSVInvalidaException(BaseImportacaoException):
    """Define ColunaCSVInvalidaException."""

    pass


class CamposObrigatoriosNaoPreenchidosException(BaseImportacaoException):
    """Define CamposObrigatoriosNaoPreenchidosException."""

    pass


class LayoutNaoConfiguradoException(BaseImportacaoException):
    """Define LayoutNaoConfiguradoException."""

    pass


class LeituraCSVException(BaseImportacaoException):
    """Define LeituraCSVException."""

    pass


class EmailFormatoInvalidoException(BaseImportacaoException):
    """Define EmailFormatoInvalidoException."""

    pass


class TipoUEDesabilitadoException(BaseImportacaoException):
    """Erro retornado pela API de Escolhas quando o tipo_ue da escola está."""

    pass


class ApiCandidatosException(BaseImportacaoException):
    """Erro de integração com o MS-Candidatos."""

    def __init__(
        self,
        mensagem: str,
        detalhes: str | None = None,
        status_code: int = 400,
        code: str | None = None,
    ) -> None:
        """Executa   init  .

        Args:
            self: Instância do objeto.
            mensagem: Parâmetro mensagem.
            detalhes: Parâmetro detalhes.
            status_code: Parâmetro status code.
            code: Parâmetro code.

        Raises:
            Nenhuma exceção específica documentada.
        """
        super().__init__(mensagem=mensagem, detalhes=detalhes)
        self.status_code = status_code
        self.code = code


class ApiEscolhasException(BaseImportacaoException):
    """Erro de integração com o MS-Escolhas."""

    def __init__(
        self,
        mensagem: str,
        detalhes: str | None = None,
        status_code: int = 400,
        code: str | None = None,
    ) -> None:
        """Executa   init  .

        Args:
            self: Instância do objeto.
            mensagem: Parâmetro mensagem.
            detalhes: Parâmetro detalhes.
            status_code: Parâmetro status code.
            code: Parâmetro code.

        Raises:
            Nenhuma exceção específica documentada.
        """
        super().__init__(mensagem=mensagem, detalhes=detalhes)
        self.status_code = status_code
        self.code = code


class ImportacaoBadRequestException(BaseImportacaoException):
    """Define ImportacaoBadRequestException."""

    pass


class ImportacaoServiceUnavailableException(BaseImportacaoException):
    """Define ImportacaoServiceUnavailableException."""

    pass


class ArquivoLotesVazioException(BaseImportacaoException):
    """Arquivo de lotes vazio ou sem dados validos."""


class ErrosValidacaoLotesException(BaseImportacaoException):
    """Arquivo de lotes contém erros de validação por linha."""


class MultiplosLotesException(BaseImportacaoException):
    """Arquivo de lotes contem mais de um valor na coluna LOTE."""


class CargoConcursoInvalidoException(BaseImportacaoException):
    """Erro quando Codigo_do_Cargo não pertence ao concurso selecionado ou."""

    pass

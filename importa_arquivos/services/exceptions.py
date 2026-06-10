"""Módulo services/exceptions."""

from __future__ import annotations


class BaseImportacaoException(Exception):
    """Erro de negócio relacionado a BaseImportacaoException."""

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
        """Retorna representação textual da mensagem do erro."""
        return self.mensagem


class ColunaCSVInvalidaException(BaseImportacaoException):
    """Erro de negócio relacionado a ColunaCSVInvalidaException."""

    pass


class CamposObrigatoriosNaoPreenchidosException(BaseImportacaoException):
    """Campos obrigatórios ausentes ou inválidos na importação."""

    pass


class LayoutNaoConfiguradoException(BaseImportacaoException):
    """Erro de negócio relacionado a LayoutNaoConfiguradoException."""

    pass


class LeituraCSVException(BaseImportacaoException):
    """Erro de negócio relacionado a LeituraCSVException."""

    pass


class EmailFormatoInvalidoException(BaseImportacaoException):
    """Erro de negócio relacionado a EmailFormatoInvalidoException."""

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
        """Inicializa a instância com os parâmetros informados.

        Args:
            mensagem: Mensagem principal do erro.
            detalhes: Detalhes complementares do erro.
            status_code: Código HTTP retornado pelo serviço externo.
            code: Código de erro de negócio.
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
        """Inicializa a instância com os parâmetros informados.

        Args:
            mensagem: Mensagem principal do erro.
            detalhes: Detalhes complementares do erro.
            status_code: Código HTTP retornado pelo serviço externo.
            code: Código de erro de negócio.
        """
        super().__init__(mensagem=mensagem, detalhes=detalhes)
        self.status_code = status_code
        self.code = code


class ImportacaoBadRequestException(BaseImportacaoException):
    """Erro de negócio relacionado a ImportacaoBadRequestException."""

    pass


class ImportacaoServiceUnavailableException(BaseImportacaoException):
    """Erro de negócio relacionado a ImportacaoServiceUnavailableException."""

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

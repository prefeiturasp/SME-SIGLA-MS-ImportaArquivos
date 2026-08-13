"""Módulo services/exceptions."""

from __future__ import annotations


class BaseImportacaoError(Exception):
    """Erro de negócio relacionado a BaseImportacaoError."""

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


class ColunaCSVInvalidaError(BaseImportacaoError):
    """Erro de negócio relacionado a ColunaCSVInvalidaError."""

    pass


class CamposObrigatoriosNaoPreenchidosError(BaseImportacaoError):
    """Campos obrigatórios ausentes ou inválidos na importação."""

    pass


class LayoutNaoConfiguradoError(BaseImportacaoError):
    """Erro de negócio relacionado a LayoutNaoConfiguradoError."""

    pass


class LeituraCSVError(BaseImportacaoError):
    """Erro de negócio relacionado a LeituraCSVError."""

    pass


class EmailFormatoInvalidoError(BaseImportacaoError):
    """Erro de negócio relacionado a EmailFormatoInvalidoError."""

    pass


class TipoUEDesabilitadoError(BaseImportacaoError):
    """Erro retornado pela API de Escolhas quando o tipo_ue da escola está."""

    pass


class ApiCandidatosError(BaseImportacaoError):
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


class ApiEscolhasError(BaseImportacaoError):
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


class ImportacaoBadRequestError(BaseImportacaoError):
    """Erro de negócio relacionado a ImportacaoBadRequestError."""

    pass


class ImportacaoServiceUnavailableError(BaseImportacaoError):
    """Erro de negócio relacionado a ImportacaoServiceUnavailableError."""

    pass


class ArquivoLotesVazioError(BaseImportacaoError):
    """Arquivo de lotes vazio ou sem dados validos."""


class ErrosValidacaoLotesError(BaseImportacaoError):
    """Arquivo de lotes contém erros de validação por linha."""


class MultiplosLotesError(BaseImportacaoError):
    """Arquivo de lotes contem mais de um valor na coluna LOTE."""


class CargoConcursoInvalidoError(BaseImportacaoError):
    """Erro quando Codigo_do_Cargo não pertence ao concurso selecionado ou."""

    pass

class BaseImportacaoException(Exception):
    def __init__(self, mensagem: str, detalhes: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.detalhes = detalhes or ""

    def __str__(self) -> str:
        return self.mensagem


class ColunaCSVInvalidaException(BaseImportacaoException):
    pass


class CamposObrigatoriosNaoPreenchidosException(BaseImportacaoException):
    pass


class LayoutNaoConfiguradoException(BaseImportacaoException):
    pass


class LeituraCSVException(BaseImportacaoException):
    pass


class EmailFormatoInvalidoException(BaseImportacaoException):
    pass


class TipoUEDesabilitadoException(BaseImportacaoException):
    """
    Erro retornado pela API de Escolhas quando o tipo_ue da escola está
    desabilitado.
    """

    pass


class ApiCandidatosException(BaseImportacaoException):
    """Erro de integração com o MS-Candidatos."""

    def __init__(
        self,
        mensagem: str,
        detalhes: str | None = None,
        status_code: int = 400,
        code: str | None = None,
    ):
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
    ):
        super().__init__(mensagem=mensagem, detalhes=detalhes)
        self.status_code = status_code
        self.code = code


class ImportacaoBadRequestException(BaseImportacaoException):
    pass


class ImportacaoServiceUnavailableException(BaseImportacaoException):
    pass


class ArquivoLotesVazioException(BaseImportacaoException):
    """Arquivo de lotes vazio ou sem dados validos."""


class ErrosValidacaoLotesException(BaseImportacaoException):
    """Arquivo de lotes contém erros de validação por linha."""


class MultiplosLotesException(BaseImportacaoException):
    """Arquivo de lotes contem mais de um valor na coluna LOTE."""


class CargoConcursoInvalidoException(BaseImportacaoException):
    """
    Erro quando Codigo_do_Cargo não pertence ao concurso selecionado ou é
    inválido.
    """

    pass

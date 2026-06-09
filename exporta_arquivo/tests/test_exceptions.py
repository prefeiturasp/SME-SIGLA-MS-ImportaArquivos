"""Testes do módulo exporta_arquivo.services.exceptions.

Sem DB, sem mocks; testes rápidos e estáveis.
"""

from __future__ import annotations

from exporta_arquivo.services.exceptions import (
    BaseExportacaoException,
    ExportacaoBadRequestException,
    ExportacaoNotFoundException,
    ExportacaoServiceUnavailableException,
)


class TestBaseExportacaoException:
    """BaseExportacaoException: mensagem e detalhes (incluindo default)."""

    def test_mensagem_e_detalhes_explicitos(self) -> None:
        """Verifica mensagem e detalhes explicitos."""
        exc = BaseExportacaoException(mensagem="Erro X", detalhes="detalhe Y")
        assert exc.mensagem == "Erro X"
        assert exc.detalhes == "detalhe Y"

    def test_detalhes_default_quando_none(self) -> None:
        """Verifica detalhes default quando none."""
        exc = BaseExportacaoException(mensagem="Só mensagem", detalhes=None)
        assert exc.mensagem == "Só mensagem"
        assert exc.detalhes == ""

    def test_str_retorna_mensagem(self) -> None:
        """Verifica str retorna mensagem."""
        exc = BaseExportacaoException(mensagem="Mensagem para usuário")
        assert str(exc) == "Mensagem para usuário"

    def test_herda_de_exception(self) -> None:
        """Verifica herda de exception."""
        exc = BaseExportacaoException(mensagem="X")
        assert isinstance(exc, Exception)


class TestExportacaoNotFoundException:
    """ExportacaoNotFoundException herda e str(exc) é a mensagem."""

    def test_herda_de_base(self) -> None:
        """Verifica herda de base."""
        exc = ExportacaoNotFoundException(
            mensagem="Não encontrado", detalhes="id inválido"
        )
        assert isinstance(exc, BaseExportacaoException)

    def test_mensagem_e_str(self) -> None:
        """Verifica mensagem e str."""
        exc = ExportacaoNotFoundException(mensagem="recurso não encontrado")
        assert exc.mensagem == "recurso não encontrado"
        assert str(exc) == "recurso não encontrado"

    def test_detalhes_persistem(self) -> None:
        """Verifica detalhes persistem."""
        exc = ExportacaoNotFoundException(
            mensagem="404", detalhes="uuid inválido"
        )
        assert exc.detalhes == "uuid inválido"


class TestExportacaoServiceUnavailableException:
    """ExportacaoServiceUnavailableException herda e str(exc) é a mensagem."""

    def test_herda_de_base(self) -> None:
        """Verifica herda de base."""
        exc = ExportacaoServiceUnavailableException(
            mensagem="Serviço indisponível", detalhes="502"
        )
        assert isinstance(exc, BaseExportacaoException)

    def test_mensagem_e_str(self) -> None:
        """Verifica mensagem e str."""
        exc = ExportacaoServiceUnavailableException(mensagem="API fora do ar")
        assert str(exc) == "API fora do ar"


class TestExportacaoBadRequestException:
    """ExportacaoBadRequestException herda e str(exc) é a mensagem."""

    def test_herda_de_base(self) -> None:
        """Verifica herda de base."""
        exc = ExportacaoBadRequestException(
            mensagem="Parâmetro inválido", detalhes="cargo_codigo"
        )
        assert isinstance(exc, BaseExportacaoException)

    def test_mensagem_e_str(self) -> None:
        """Verifica mensagem e str."""
        exc = ExportacaoBadRequestException(
            mensagem="cargo_codigo é obrigatório"
        )
        assert str(exc) == "cargo_codigo é obrigatório"

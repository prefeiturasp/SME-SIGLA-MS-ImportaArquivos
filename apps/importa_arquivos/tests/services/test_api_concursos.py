"""Módulo tests/services/test_api_concursos."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from importa_arquivos.services.api_concursos import ApiConcursosService
from importa_arquivos.services.exceptions import CargoConcursoInvalidoException


def _make_service() -> Any:
    """Make service."""
    return ApiConcursosService(
        base_url="http://concursos-api", timeout_seconds=5
    )


def test_obter_codigos_cargo_sucesso() -> None:
    """Verifica obter codigos cargo sucesso."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "uuid": "abc",
        "nome": "Concurso X",
        "cargos": [
            {"uuid": "1", "nome": "Cargo A", "codigo": 10},
            {"uuid": "2", "nome": "Cargo B", "codigo": 20},
        ],
    }
    with patch(
        "importa_arquivos.services.api_concursos.requests.get",
        return_value=mock_resp,
    ):
        codigos = _make_service().obter_codigos_cargo_do_concurso(
            "uuid-concurso"
        )
    assert codigos == {10, 20}


def test_obter_codigos_cargo_sem_cargos() -> None:
    """Verifica obter codigos cargo sem cargos."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"uuid": "abc", "cargos": []}
    with patch(
        "importa_arquivos.services.api_concursos.requests.get",
        return_value=mock_resp,
    ):
        codigos = _make_service().obter_codigos_cargo_do_concurso(
            "uuid-concurso"
        )
    assert codigos == set()


def test_obter_codigos_cargo_404_lanca_excecao() -> None:
    """Verifica obter codigos cargo 404 lanca excecao."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with (
        patch(
            "importa_arquivos.services.api_concursos.requests.get",
            return_value=mock_resp,
        ),
        pytest.raises(CargoConcursoInvalidoException) as exc,
    ):
        _make_service().obter_codigos_cargo_do_concurso("uuid-invalido")
    assert "concurso" in exc.value.mensagem.lower()


def test_obter_codigos_cargo_erro_conexao_lanca_excecao() -> None:
    """Verifica obter codigos cargo erro conexao lanca excecao."""
    from requests.exceptions import RequestException

    with (
        patch(
            "importa_arquivos.services.api_concursos.requests.get",
            side_effect=RequestException("timeout"),
        ),
        pytest.raises(CargoConcursoInvalidoException) as exc,
    ):
        _make_service().obter_codigos_cargo_do_concurso("uuid-concurso")
    assert "indisponível" in exc.value.mensagem.lower()


def test_obter_codigos_cargo_5xx_lanca_excecao() -> None:
    """Verifica obter codigos cargo 5xx lanca excecao."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    with (
        patch(
            "importa_arquivos.services.api_concursos.requests.get",
            return_value=mock_resp,
        ),
        pytest.raises(CargoConcursoInvalidoException),
    ):
        _make_service().obter_codigos_cargo_do_concurso("uuid-concurso")

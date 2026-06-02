from unittest.mock import MagicMock, patch

import pytest

from importa_arquivos.services.api_concursos import ApiConcursosService
from importa_arquivos.services.exceptions import CargoConcursoInvalidoException


def _make_service():
    return ApiConcursosService(
        base_url="http://concursos-api", timeout_seconds=5
    )


def test_obter_codigos_cargo_sucesso():
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


def test_obter_codigos_cargo_sem_cargos():
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


def test_obter_codigos_cargo_404_lanca_excecao():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch(  # noqa: SIM117
        "importa_arquivos.services.api_concursos.requests.get",
        return_value=mock_resp,
    ):
        with pytest.raises(CargoConcursoInvalidoException) as exc:
            _make_service().obter_codigos_cargo_do_concurso("uuid-invalido")
    assert "concurso" in exc.value.mensagem.lower()


def test_obter_codigos_cargo_erro_conexao_lanca_excecao():
    from requests.exceptions import RequestException

    with patch(  # noqa: SIM117
        "importa_arquivos.services.api_concursos.requests.get",
        side_effect=RequestException("timeout"),
    ):
        with pytest.raises(CargoConcursoInvalidoException) as exc:
            _make_service().obter_codigos_cargo_do_concurso("uuid-concurso")
    assert "indisponível" in exc.value.mensagem.lower()


def test_obter_codigos_cargo_5xx_lanca_excecao():
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    with patch(  # noqa: SIM117
        "importa_arquivos.services.api_concursos.requests.get",
        return_value=mock_resp,
    ):
        with pytest.raises(CargoConcursoInvalidoException):
            _make_service().obter_codigos_cargo_do_concurso("uuid-concurso")

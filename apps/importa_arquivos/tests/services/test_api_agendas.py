"""Testes do serviço de agendas."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
from requests import RequestException

from importa_arquivos.services.api_agendas import ApiAgendasService
from importa_arquivos.services.exceptions import ApiAgendasError

pytestmark = pytest.mark.django_db


def test_buscar_por_processo_convocacao_uuid(settings: Any) -> None:
    """GET com processo_convocacao_uuid devolve results."""
    settings.AGENDAS_API_URL = "https://api.agendas"
    settings.AGENDAS_API_KEY = "key-agenda"
    processo_uuid = "11111111-1111-1111-1111-111111111111"
    with patch("sigla_sdk.http.api_client.http_client.get") as mock_get:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "processo_convocacao_uuid": processo_uuid,
                    "modalidade": "ONLINE",
                }
            ]
        }
        mock_get.return_value = mock_resp
        resultados = ApiAgendasService().buscar_por_processo_convocacao_uuid(
            processo_uuid
        )
    assert len(resultados) == 1
    assert resultados[0]["modalidade"] == "ONLINE"
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.agendas/api/v1/agendas/"
    assert kwargs["params"] == {"processo_convocacao_uuid": processo_uuid}


def test_buscar_agendas_erro_http(settings: Any) -> None:
    """Status HTTP >= 400 gera ApiAgendasError."""
    settings.AGENDAS_API_URL = "https://api.agendas"
    with patch("sigla_sdk.http.api_client.http_client.get") as mock_get:
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "erro"
        mock_get.return_value = mock_resp
        with pytest.raises(ApiAgendasError):
            ApiAgendasService().buscar_por_processo_convocacao_uuid("x")


def test_buscar_agendas_request_exception(settings: Any) -> None:
    """Falha de rede propaga RequestException."""
    settings.AGENDAS_API_URL = "https://api.agendas"
    with patch(
        "sigla_sdk.http.api_client.http_client.get",
        side_effect=RequestException("timeout"),
    ):
        with pytest.raises(RequestException):
            ApiAgendasService().buscar_por_processo_convocacao_uuid("x")

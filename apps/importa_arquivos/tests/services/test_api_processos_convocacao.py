"""Testes do serviço de processos de convocação."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
from requests import RequestException

from importa_arquivos.services.api_processos_convocacao import (
    PROCESSO_ID_PRODAM_PADRAO,
    ApiProcessosConvocacaoService,
)
from importa_arquivos.services.exceptions import ApiProcessosConvocacaoError

pytestmark = pytest.mark.django_db


def test_listar_pendentes_retorna_results(settings: Any) -> None:
    """GET com status=PENDENTE devolve a lista de results."""
    settings.PROCESSOS_CONVOCACAO_API_URL = "https://api.processos"
    settings.PROCESSOS_CONVOCACAO_API_KEY = "key-teste"
    processo_uuid = "11111111-1111-1111-1111-111111111111"
    concurso_uuid = "22222222-2222-2222-2222-222222222222"
    with patch("sigla_sdk.http.api_client.http_client.get") as mock_get:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "uuid": processo_uuid,
                    "concurso_uuid": concurso_uuid,
                    "status": "PENDENTE",
                }
            ],
            "next": None,
        }
        mock_get.return_value = mock_resp
        resultados = ApiProcessosConvocacaoService().listar_pendentes()
    assert len(resultados) == 1
    assert resultados[0]["uuid"] == processo_uuid
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.processos/api/v1/processos-convocacao/"
    assert kwargs["params"] == {"status": "PENDENTE"}


def test_listar_pendentes_erro_http(settings: Any) -> None:
    """Status HTTP >= 400 gera ApiProcessosConvocacaoError."""
    settings.PROCESSOS_CONVOCACAO_API_URL = "https://api.processos"
    with patch("sigla_sdk.http.api_client.http_client.get") as mock_get:
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "erro interno"
        mock_get.return_value = mock_resp
        with pytest.raises(ApiProcessosConvocacaoError):
            ApiProcessosConvocacaoService().listar_pendentes()


def test_listar_pendentes_request_exception(settings: Any) -> None:
    """Falha de rede propaga RequestException."""
    settings.PROCESSOS_CONVOCACAO_API_URL = "https://api.processos"
    with patch(
        "sigla_sdk.http.api_client.http_client.get",
        side_effect=RequestException("timeout"),
    ):
        with pytest.raises(RequestException):
            ApiProcessosConvocacaoService().listar_pendentes()


def test_extrair_processo_uuid_e_id_mapeia_uuid_e_fallback_id() -> None:
    """Mapeia uuid -> processo_uuid e usa 819 quando não há processo_id."""
    processo_uuid = "11111111-1111-1111-1111-111111111111"
    concurso_uuid = "22222222-2222-2222-2222-222222222222"
    extraidos = ApiProcessosConvocacaoService.extrair_processo_uuid_e_id(
        [
            {
                "uuid": processo_uuid,
                "concurso_uuid": concurso_uuid,
            }
        ]
    )
    assert extraidos == [
        {
            "processo_uuid": processo_uuid,
            "processo_id": PROCESSO_ID_PRODAM_PADRAO,
            "concurso_uuid": concurso_uuid,
        }
    ]


def test_extrair_processo_uuid_e_id_usa_processo_id_do_payload() -> None:
    """Respeita processo_id quando vier no payload da API."""
    extraidos = ApiProcessosConvocacaoService.extrair_processo_uuid_e_id(
        [
            {
                "processo_uuid": "11111111-1111-1111-1111-111111111111",
                "processo_id": 42,
                "concurso_uuid": "22222222-2222-2222-2222-222222222222",
            }
        ]
    )
    assert extraidos[0]["processo_id"] == 42


def test_extrair_ignora_sem_uuid_ou_concurso() -> None:
    """Itens incompletos são descartados."""
    extraidos = ApiProcessosConvocacaoService.extrair_processo_uuid_e_id(
        [
            {"uuid": "11111111-1111-1111-1111-111111111111"},
            {"concurso_uuid": "22222222-2222-2222-2222-222222222222"},
        ]
    )
    assert extraidos == []

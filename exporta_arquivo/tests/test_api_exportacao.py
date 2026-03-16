"""
Testes dos clientes de API externa (ApiCandidatosService, ApiEscolhasService).
Mock de requests: timeout, 5xx, JSON inválido → exceções do domínio (ExportacaoServiceUnavailableException, etc.).
Usados apenas pelo exporta_arquivo; sem duplicar testes de outros apps.
"""
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import Timeout

from exporta_arquivo.services.api_candidatos import ApiCandidatosService
from exporta_arquivo.services.api_escolhas import ApiEscolhasService
from exporta_arquivo.services.exceptions import (
    ExportacaoNotFoundException,
    ExportacaoServiceUnavailableException,
)


# --- ApiCandidatosService ---


class TestApiCandidatosService:
    """get_habilitados: timeout, 5xx, JSON inválido → ServiceUnavailable; 404 → NotFound."""

    @pytest.fixture
    def service(self):
        return ApiCandidatosService(base_url="http://test", timeout_seconds=5)

    def test_timeout_levanta_service_unavailable(self, service):
        with patch("exporta_arquivo.services.api_candidatos.requests.get", side_effect=Timeout()):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_habilitados("proc-uuid", 100)
            assert "indisponível" in exc_info.value.mensagem.lower() or "habilitados" in exc_info.value.mensagem.lower()

    def test_5xx_levanta_service_unavailable(self, service):
        resp = MagicMock()
        resp.status_code = 503
        resp.text = "Service Unavailable"
        with patch("exporta_arquivo.services.api_candidatos.requests.get", return_value=resp):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_habilitados("proc-uuid", 100)
            assert "503" in exc_info.value.detalhes or "indisponível" in exc_info.value.mensagem.lower()

    def test_resposta_nao_json_levanta_service_unavailable(self, service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("Invalid JSON")
        with patch("exporta_arquivo.services.api_candidatos.requests.get", return_value=resp):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_habilitados("proc-uuid", 100)
            assert "inválida" in exc_info.value.mensagem.lower() or "resposta" in exc_info.value.mensagem.lower()

    def test_404_levanta_not_found(self, service):
        resp = MagicMock()
        resp.status_code = 404
        with patch("exporta_arquivo.services.api_candidatos.requests.get", return_value=resp):
            with pytest.raises(ExportacaoNotFoundException) as exc_info:
                service.get_habilitados("proc-uuid", 100)
            assert "não encontrado" in exc_info.value.mensagem.lower() or "habilitados" in exc_info.value.mensagem.lower()

    def test_200_lista_retorna_lista(self, service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": 1}]
        with patch("exporta_arquivo.services.api_candidatos.requests.get", return_value=resp):
            out = service.get_habilitados("proc-uuid", 100)
        assert out == [{"id": 1}]

    def test_200_results_retorna_results(self, service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"results": [{"id": 1}]}
        with patch("exporta_arquivo.services.api_candidatos.requests.get", return_value=resp):
            out = service.get_habilitados("proc-uuid", 100)
        assert out == [{"id": 1}]


# --- ApiEscolhasService ---


class TestApiEscolhasService:
    """get_vagas_escolas: timeout, 5xx, JSON inválido → ServiceUnavailable."""

    @pytest.fixture
    def service(self):
        return ApiEscolhasService(base_url="http://test", timeout_seconds=5)

    def test_timeout_levanta_service_unavailable(self, service):
        with patch("exporta_arquivo.services.api_escolhas.requests.get", side_effect=Timeout()):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_vagas_escolas("proc-uuid", 100)
            assert "indisponível" in exc_info.value.mensagem.lower() or "vagas" in exc_info.value.mensagem.lower()

    def test_5xx_levanta_service_unavailable(self, service):
        resp = MagicMock()
        resp.status_code = 502
        resp.text = "Bad Gateway"
        with patch("exporta_arquivo.services.api_escolhas.requests.get", return_value=resp):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_vagas_escolas("proc-uuid", 100)
            assert "502" in exc_info.value.detalhes or "indisponível" in exc_info.value.mensagem.lower()

    def test_resposta_nao_json_levanta_service_unavailable(self, service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("Invalid JSON")
        with patch("exporta_arquivo.services.api_escolhas.requests.get", return_value=resp):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_vagas_escolas("proc-uuid", 100)
            assert "inválida" in exc_info.value.mensagem.lower() or "resposta" in exc_info.value.mensagem.lower()

    def test_200_dict_retorna_dict(self, service):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"vagas": []}
        with patch("exporta_arquivo.services.api_escolhas.requests.get", return_value=resp):
            out = service.get_vagas_escolas("proc-uuid", 100)
        assert out == {"vagas": []}

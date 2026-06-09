"""Testes dos clientes de API externa (ApiCandidatosService, ApiEscolhasService).

Mock de requests: timeout, 5xx, JSON inválido → exceções do domínio
(CandidatosServiceUnavailableException, EscolhasServiceUnavailableException,
etc.).
Usados apenas pelo exporta_arquivo; sem duplicar testes de outros apps.
"""
from __future__ import annotations
from typing import Any
from unittest.mock import MagicMock, patch
import pytest
from requests.exceptions import Timeout
from exporta_arquivo.services.api_candidatos import ApiCandidatosService
from exporta_arquivo.services.api_escolhas import ApiEscolhasService
from exporta_arquivo.services.exceptions import CandidatosNotFoundException, CandidatosServiceUnavailableException, EscolhasServiceUnavailableException

class TestApiCandidatosService:
    """get_habilitados: timeout, 5xx, JSON inválido → ServiceUnavailable; 404 →.

    NotFound.
    """

    @pytest.fixture
    def service(self) -> Any:
        """Executa service."""
        return ApiCandidatosService(base_url='http://test', timeout_seconds=5)

    def test_timeout_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica timeout levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', side_effect=Timeout()):
            with pytest.raises(CandidatosServiceUnavailableException) as exc_info:
                service.get_habilitados(processo_uuid='proc-uuid', cargo_codigo=100)
            assert 'indisponível' in exc_info.value.mensagem.lower() or 'habilitados' in exc_info.value.mensagem.lower()

    def test_5xx_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica 5xx levanta service unavailable."""
        resp = MagicMock()
        resp.status_code = 503
        resp.text = 'Service Unavailable'
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            with pytest.raises(CandidatosServiceUnavailableException) as exc_info:
                service.get_habilitados(processo_uuid='proc-uuid', cargo_codigo=100)
            assert '503' in exc_info.value.detalhes or 'indisponível' in exc_info.value.mensagem.lower()

    def test_resposta_nao_json_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica resposta nao json levanta service unavailable."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError('Invalid JSON')
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            with pytest.raises(CandidatosServiceUnavailableException) as exc_info:
                service.get_habilitados(processo_uuid='proc-uuid', cargo_codigo=100)
            assert 'inválida' in exc_info.value.mensagem.lower() or 'resposta' in exc_info.value.mensagem.lower()

    def test_404_levanta_not_found(self, service: Any) -> None:
        """Verifica 404 levanta not found."""
        resp = MagicMock()
        resp.status_code = 404
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            with pytest.raises(CandidatosNotFoundException) as exc_info:
                service.get_habilitados(processo_uuid='proc-uuid', cargo_codigo=100)
            assert 'não encontrado' in exc_info.value.mensagem.lower() or 'habilitados' in exc_info.value.mensagem.lower()

    def test_200_lista_retorna_lista(self, service: Any) -> None:
        """Verifica 200 lista retorna lista."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{'id': 1}]
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            out = service.get_habilitados(processo_uuid='proc-uuid', cargo_codigo=100)
        assert out == [{'id': 1}]

    def test_200_results_retorna_results(self, service: Any) -> None:
        """Verifica 200 results retorna results."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'results': [{'id': 1}]}
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            out = service.get_habilitados(processo_uuid='proc-uuid', cargo_codigo=100)
        assert out == [{'id': 1}]

class TestApiEscolhasService:
    """get_vagas_escolas: timeout, 5xx, JSON inválido → ServiceUnavailable."""

    @pytest.fixture
    def service(self) -> Any:
        """Executa service."""
        return ApiEscolhasService(base_url='http://test', timeout_seconds=5)

    def test_timeout_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica timeout levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', side_effect=Timeout()):
            with pytest.raises(EscolhasServiceUnavailableException) as exc_info:
                service.get_vagas_escolas('proc-uuid', 100)
            assert 'indisponível' in exc_info.value.mensagem.lower() or 'vagas' in exc_info.value.mensagem.lower()

    def test_5xx_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica 5xx levanta service unavailable."""
        resp = MagicMock()
        resp.status_code = 502
        resp.text = 'Bad Gateway'
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            with pytest.raises(EscolhasServiceUnavailableException) as exc_info:
                service.get_vagas_escolas('proc-uuid', 100)
            assert '502' in exc_info.value.detalhes or 'indisponível' in exc_info.value.mensagem.lower()

    def test_resposta_nao_json_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica resposta nao json levanta service unavailable."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError('Invalid JSON')
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            with pytest.raises(EscolhasServiceUnavailableException) as exc_info:
                service.get_vagas_escolas('proc-uuid', 100)
            assert 'inválida' in exc_info.value.mensagem.lower() or 'resposta' in exc_info.value.mensagem.lower()

    def test_200_dict_retorna_dict(self, service: Any) -> None:
        """Verifica 200 dict retorna dict."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {'vagas': []}
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=resp):
            out = service.get_vagas_escolas('proc-uuid', 100)
        assert out == {'vagas': []}

"""Testes dos clientes de API do módulo api_lote.py:.

- ApiLoteCandidatosService._fazer_request_get: 404, 5xx, timeout, JSON
inválido, non-200, 200 lista/results
- ApiLoteCandidatosService.get_candidatos_lote: parâmetros corretos
- ApiLoteCandidatosService.get_candidatos_por_numero_lote: parâmetros corretos
- ApiLoteEscolhasService.get_escolhas_lote: 5xx, timeout, JSON inválido,
non-200, 200 lista/results, payload POST correto
Sem DB.
"""
from __future__ import annotations
from typing import Any
from unittest.mock import MagicMock, patch
import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout
from exporta_arquivo.services.api_lote import ApiLoteCandidatosService, ApiLoteEscolhasService
from exporta_arquivo.services.exceptions import ExportacaoNotFoundException, ExportacaoServiceUnavailableException

def _mock_response(status_code: Any=200, json_data: Any=None, raise_json: Any=False, text: Any='') -> Any:
    """Executa  mock response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    if raise_json:
        resp.json.side_effect = ValueError('Invalid JSON')
    else:
        resp.json.return_value = json_data if json_data is not None else []
    return resp

class TestApiLoteCandidatosServiceFazerRequestGet:
    """_fazer_request_get: erros de rede e de protocolo → exceções do domínio."""

    @pytest.fixture
    def service(self) -> Any:
        """Executa service."""
        return ApiLoteCandidatosService(base_url='http://test', timeout_seconds=5)

    def test_timeout_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica timeout levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', side_effect=Timeout()):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert 'indisponível' in exc_info.value.mensagem.lower()

    def test_connection_error_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica connection error levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', side_effect=RequestsConnectionError()):
            with pytest.raises(ExportacaoServiceUnavailableException):
                service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')

    def test_404_levanta_not_found(self, service: Any) -> None:
        """Verifica 404 levanta not found."""
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=404)):
            with pytest.raises(ExportacaoNotFoundException) as exc_info:
                service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert 'não encontrado' in exc_info.value.mensagem.lower()

    def test_500_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica 500 levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=500, text='Internal Server Error')):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert '500' in exc_info.value.detalhes

    def test_503_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica 503 levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=503, text='Service Unavailable')):
            with pytest.raises(ExportacaoServiceUnavailableException):
                service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')

    def test_non_200_nao_5xx_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica non 200 nao 5xx levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=422)):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert '422' in exc_info.value.detalhes

    def test_json_invalido_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica json invalido levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=200, raise_json=True)):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert 'inválid' in exc_info.value.mensagem.lower()

    def test_200_lista_retorna_lista(self, service: Any) -> None:
        """Verifica 200 lista retorna lista."""
        dados = [{'uuid': 'abc', 'nome': 'João'}]
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=200, json_data=dados)):
            result = service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert result == dados

    def test_200_dict_com_results_retorna_lista(self, service: Any) -> None:
        """Verifica 200 dict com results retorna lista."""
        dados = {'results': [{'uuid': 'xyz'}], 'count': 1}
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=200, json_data=dados)):
            result = service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert result == [{'uuid': 'xyz'}]

    def test_200_dict_sem_results_retorna_lista_vazia(self, service: Any) -> None:
        """Verifica 200 dict sem results retorna lista vazia."""
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=200, json_data={'outro': 'campo'})):
            result = service._fazer_request_get('http://test/api/v1/habilitados/', {}, 'lote')
        assert result == []

class TestApiLoteCandidatosGetCandidatosLote:
    """get_candidatos_lote: delega a _fazer_request_get com parâmetro lote__uuid."""

    @pytest.fixture
    def service(self) -> Any:
        """Executa service."""
        return ApiLoteCandidatosService(base_url='http://test', timeout_seconds=5)

    def test_passa_lote_uuid_como_parametro(self, service: Any) -> None:
        """Verifica passa lote uuid como parametro."""
        lote_uuid = 'aaaa-bbbb-cccc'
        with patch.object(service, '_fazer_request_get', return_value=[]) as mock_req:
            service.get_candidatos_lote(lote_uuid)
        _, kwargs = mock_req.call_args if mock_req.call_args.kwargs else (mock_req.call_args.args, {})
        args = mock_req.call_args.args
        assert args[1] == {'lote__uuid': lote_uuid}

    def test_retorna_lista_da_api(self, service: Any) -> None:
        """Verifica retorna lista da api."""
        esperado = [{'uuid': 'abc'}]
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=200, json_data=esperado)):
            result = service.get_candidatos_lote('lote-uuid-123')
        assert result == esperado

class TestApiLoteCandidatosGetPorNumeroLote:
    """get_candidatos_por_numero_lote: parâmetros lote__concurso_uuid e.

    numero_lote.
    """

    @pytest.fixture
    def service(self) -> Any:
        """Executa service."""
        return ApiLoteCandidatosService(base_url='http://test', timeout_seconds=5)

    def test_passa_concurso_uuid_e_numero_lote(self, service: Any) -> None:
        """Verifica passa concurso uuid e numero lote."""
        with patch.object(service, '_fazer_request_get', return_value=[]) as mock_req:
            service.get_candidatos_por_numero_lote('concurso-uuid-123', 7)
        args = mock_req.call_args.args
        params = args[1]
        assert params['lote__concurso_uuid'] == 'concurso-uuid-123'
        assert params['numero_lote'] == 7

    def test_retorna_lista_da_api(self, service: Any) -> None:
        """Verifica retorna lista da api."""
        esperado = [{'uuid': 'def'}]
        with patch('sigla_sdk.http.api_client.http_client.get', return_value=_mock_response(status_code=200, json_data=esperado)):
            result = service.get_candidatos_por_numero_lote('concurso-uuid', 3)
        assert result == esperado

class TestApiLoteEscolhasServiceGetEscolhasLote:
    """get_escolhas_lote: POST com payload correto; timeout, 5xx, JSON inválido,.

    non-200 → exceções.
    """

    @pytest.fixture
    def service(self) -> Any:
        """Executa service."""
        return ApiLoteEscolhasService(base_url='http://test', timeout_seconds=5)

    def test_timeout_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica timeout levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.post', side_effect=Timeout()):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_escolhas_lote(['uuid1'], 'concurso-uuid')
        assert 'indisponível' in exc_info.value.mensagem.lower()

    def test_500_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica 500 levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.post', return_value=_mock_response(status_code=500, text='err')):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_escolhas_lote(['uuid1'], 'concurso-uuid')
        assert '500' in exc_info.value.detalhes

    def test_non_200_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica non 200 levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.post', return_value=_mock_response(status_code=400)):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_escolhas_lote(['uuid1'], 'concurso-uuid')
        assert '400' in exc_info.value.detalhes

    def test_json_invalido_levanta_service_unavailable(self, service: Any) -> None:
        """Verifica json invalido levanta service unavailable."""
        with patch('sigla_sdk.http.api_client.http_client.post', return_value=_mock_response(status_code=200, raise_json=True)):
            with pytest.raises(ExportacaoServiceUnavailableException) as exc_info:
                service.get_escolhas_lote(['uuid1'], 'concurso-uuid')
        assert 'inválid' in exc_info.value.mensagem.lower()

    def test_200_lista_retorna_lista(self, service: Any) -> None:
        """Verifica 200 lista retorna lista."""
        dados = [{'candidato_uuid': 'uuid1', 'situacao': 'escolha'}]
        with patch('sigla_sdk.http.api_client.http_client.post', return_value=_mock_response(status_code=200, json_data=dados)):
            result = service.get_escolhas_lote(['uuid1'], 'concurso-uuid')
        assert result == dados

    def test_200_dict_com_results_retorna_lista(self, service: Any) -> None:
        """Verifica 200 dict com results retorna lista."""
        dados = {'results': [{'candidato_uuid': 'uuid2'}]}
        with patch('sigla_sdk.http.api_client.http_client.post', return_value=_mock_response(status_code=200, json_data=dados)):
            result = service.get_escolhas_lote(['uuid2'], 'concurso-uuid')
        assert result == [{'candidato_uuid': 'uuid2'}]

    def test_payload_post_contem_candidato_uuids_e_concurso_uuid(self, service: Any) -> None:
        """Verifica payload post contem candidato uuids e concurso uuid."""
        uuids = ['uuid-a', 'uuid-b']
        concurso = 'concurso-xyz'
        with patch('sigla_sdk.http.api_client.http_client.post', return_value=_mock_response(status_code=200, json_data=[])) as mock_post:
            service.get_escolhas_lote(uuids, concurso)
        _, kwargs = mock_post.call_args
        payload = kwargs.get('json', {})
        assert payload['candidato_uuid'] == uuids
        assert payload['concurso_uuid'] == concurso

    def test_uuids_convertidos_para_string_no_payload(self, service: Any) -> None:
        """Verifica uuids convertidos para string no payload."""
        import uuid as _uuid_mod
        u = _uuid_mod.uuid4()
        with patch('sigla_sdk.http.api_client.http_client.post', return_value=_mock_response(status_code=200, json_data=[])) as mock_post:
            service.get_escolhas_lote([u], 'concurso-uuid')
        _, kwargs = mock_post.call_args
        payload = kwargs.get('json', {})
        assert all((isinstance(v, str) for v in payload['candidato_uuid']))

"""
Testes unitários para ApiProdamService.
"""

import json
from unittest.mock import Mock, patch

import pytest
from requests import RequestException

from importa_arquivos.models import LogRequestHttp
from importa_arquivos.services.api_prodam import ApiProdamService

pytestmark = pytest.mark.django_db


class TestApiProdamService:
    """Testes para ApiProdamService."""

    def test_init_com_configuracoes_validas(self, settings):
        """Testa inicialização com configurações válidas."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        assert service.api_url == "https://api.prodam.com/endpoint"
        assert service._token == "token123"
        assert service._usuario == "usuario"
        assert service._senha == "senha"
        assert service.timeout_seconds == 300

    def test_init_com_timeout_customizado(self, settings):
        """Testa inicialização com timeout customizado."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService(timeout_seconds=60)

        assert service.timeout_seconds == 60

    def test_init_sem_token_levanta_erro(self, settings):
        """Testa que falta de token levanta ValueError."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = None
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        with pytest.raises(
            ValueError, match="Configurações da API externa não encontradas"
        ):
            ApiProdamService()

    def test_init_sem_usuario_levanta_erro(self, settings):
        """Testa que falta de usuário levanta ValueError."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = None
        settings.PRODAM_API_SENHA = "senha"

        with pytest.raises(
            ValueError, match="Configurações da API externa não encontradas"
        ):
            ApiProdamService()

    def test_init_sem_senha_levanta_erro(self, settings):
        """Testa que falta de senha levanta ValueError."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = None

        with pytest.raises(
            ValueError, match="Configurações da API externa não encontradas"
        ):
            ApiProdamService()

    def test_get_headers_retorna_headers_corretos(self, settings):
        """Testa que _get_headers retorna headers corretos."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()
        headers = service._get_headers()

        assert headers["Authorization"] == "Basic token123"
        assert headers["Content-Type"] == "application/json"

    def test_consultar_resultado_convocacao_ingresso_sucesso(self, settings):
        """Testa consulta bem-sucedida à API Prodam."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        resposta_mock = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [
                {
                    "codigoPessoaFisica": "12345678901",
                    "codigoCargo": "123",
                    "descricaoStatus": "ALOCADO",
                }
            ],
        }

        with patch(
            "importa_arquivos.services.api_prodam.requests.post"
        ) as mock_post:
            mock_resp = Mock()
            mock_resp.text = '{"retorno": "TRUE", "mensagem": "Sucesso", "lstDadosResultadoConvocacaoIngresso": [{"codigoPessoaFisica": "12345678901", "codigoCargo": "123", "descricaoStatus": "ALOCADO"}]}'  # noqa: E501
            mock_resp.json.side_effect = [
                resposta_mock,
                json.dumps(resposta_mock),
            ]
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            resultado = service.consultar_resultado_convocacao_ingresso(
                processo_id=123
            )

            assert resultado["retorno"] == "TRUE"
            assert len(resultado["lstDadosResultadoConvocacaoIngresso"]) == 1

            assert LogRequestHttp.objects.filter(processo_id=123).exists()

    def test_consultar_resultado_convocacao_ingresso_cria_log(self, settings):
        """Testa que um log é criado após a requisição."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        resposta_mock = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [],
        }

        with patch(
            "importa_arquivos.services.api_prodam.requests.post"
        ) as mock_post:
            mock_resp = Mock()
            mock_resp.text = '{"retorno": "TRUE", "mensagem": "Sucesso", "lstDadosResultadoConvocacaoIngresso": []}'  # noqa: E501
            mock_resp.json.side_effect = [
                resposta_mock,
                json.dumps(resposta_mock),
            ]
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            service.consultar_resultado_convocacao_ingresso(processo_id=456)

            log = LogRequestHttp.objects.get(processo_id=456)
            assert log.url == "https://api.prodam.com/endpoint"
            assert log.metodo_http == "POST"
            assert log.processo_id == 456
            assert "retorno" in log.resposta_raw

    def test_consultar_resultado_convocacao_ingresso_payload_correto(
        self, settings
    ):
        """Testa que o payload enviado está correto."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        resposta_mock = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [],
        }

        with patch(
            "importa_arquivos.services.api_prodam.requests.post"
        ) as mock_post:
            mock_resp = Mock()
            mock_resp.text = json.dumps(resposta_mock)
            mock_resp.json.side_effect = [
                resposta_mock,
                json.dumps(resposta_mock),
            ]
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            service.consultar_resultado_convocacao_ingresso(processo_id=789)

            args, kwargs = mock_post.call_args
            assert args[0] == "https://api.prodam.com/endpoint"
            assert kwargs["headers"]["Authorization"] == "Basic token123"
            assert kwargs["json"]["usuario"] == "usuario"
            assert kwargs["json"]["senha"] == "senha"
            assert kwargs["json"]["identificadorChamadaSistema"] == 789
            assert kwargs["timeout"] == 300

    def test_consultar_resultado_convocacao_ingresso_request_exception(
        self, settings
    ):
        """Testa tratamento de RequestException."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        with patch(  # noqa: SIM117
            "importa_arquivos.services.api_prodam.requests.post",
            side_effect=RequestException("Erro de conexão"),
        ):
            with pytest.raises(
                RequestException, match="Erro ao consultar API externa"
            ):
                service.consultar_resultado_convocacao_ingresso(
                    processo_id=123
                )

    def test_consultar_resultado_convocacao_ingresso_resposta_invalida(
        self, settings
    ):
        """Testa tratamento de resposta inválida."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        resposta_mock = {
            "retorno": "TRUE",
        }

        with patch(
            "importa_arquivos.services.api_prodam.requests.post"
        ) as mock_post:
            mock_resp = Mock()
            mock_resp.text = "{}"
            mock_resp.json.side_effect = [
                resposta_mock,
                json.dumps(resposta_mock),
            ]
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            with pytest.raises(
                ValueError, match="Erro ao processar resposta da API externa"
            ):
                service.consultar_resultado_convocacao_ingresso(
                    processo_id=123
                )

    def test_consultar_resultado_convocacao_ingresso_resposta_com_erro_validacao(  # noqa: E501
        self, settings
    ):
        """
        Testa tratamento quando resposta não passa na validação do serializer.
        """
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        resposta_mock = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [
                {
                    "codigoPessoaFisica": "12345678901",
                }
            ],
        }

        with patch(
            "importa_arquivos.services.api_prodam.requests.post"
        ) as mock_post:
            mock_resp = Mock()
            mock_resp.text = "{}"
            mock_resp.json.side_effect = [
                resposta_mock,
                json.dumps(resposta_mock),
            ]
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            with pytest.raises(
                ValueError, match="Erro ao processar resposta da API externa"
            ):
                service.consultar_resultado_convocacao_ingresso(
                    processo_id=123
                )

    def test_consultar_resultado_convocacao_ingresso_nao_quebra_quando_log_falha(  # noqa: E501
        self, settings
    ):
        """Testa que não quebra quando criação de log falha."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        resposta_mock = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [],
        }

        with patch(
            "importa_arquivos.services.api_prodam.requests.post"
        ) as mock_post:
            mock_resp = Mock()
            mock_resp.text = json.dumps(resposta_mock)
            mock_resp.json.side_effect = [
                resposta_mock,
                json.dumps(resposta_mock),
            ]
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            with patch(
                "importa_arquivos.services.api_prodam.LogRequestHttp.objects.create",
                side_effect=Exception("Erro ao criar log"),
            ):
                resultado = service.consultar_resultado_convocacao_ingresso(
                    processo_id=123
                )
                assert resultado["retorno"] == "TRUE"

    def test_consultar_resultado_convocacao_ingresso_http_error(
        self, settings
    ):
        """Testa tratamento de erro HTTP."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"

        service = ApiProdamService()

        with patch(
            "importa_arquivos.services.api_prodam.requests.post"
        ) as mock_post:
            mock_resp = Mock()
            mock_resp.text = "Erro 500"
            mock_resp.json.return_value = {"erro": "500 Internal Server Error"}
            mock_resp.raise_for_status.side_effect = RequestException(
                "500 Internal Server Error"
            )
            mock_post.return_value = mock_resp

            with pytest.raises(RequestException):
                service.consultar_resultado_convocacao_ingresso(
                    processo_id=123
                )

            assert LogRequestHttp.objects.filter(processo_id=123).exists()

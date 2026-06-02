"""
Testes unitários para o model LogRequestHttp.
"""

import pytest

from importa_arquivos.models import LogRequestHttp

pytestmark = pytest.mark.django_db


class TestLogRequestHttpModel:
    """Testes para o model LogRequestHttp."""

    def test_criar_log_request_http_com_valores_minimos(self):
        """Testa criação de log com valores mínimos."""
        log = LogRequestHttp.objects.create(
            url="https://api.example.com/endpoint",
            metodo_http="POST",
            resposta_raw='{"status": "ok"}',
        )

        assert log.uuid is not None
        assert log.url == "https://api.example.com/endpoint"
        assert log.metodo_http == "POST"
        assert log.resposta_raw == '{"status": "ok"}'
        assert log.processo_id is None
        assert log.criado_em is not None
        assert log.atualizado_em is not None

    def test_criar_log_request_http_com_todos_campos(self):
        """Testa criação de log com todos os campos preenchidos."""
        processo_id = 123
        url = "https://api.example.com/endpoint"
        metodo = "GET"
        resposta = '{"data": "test"}'

        log = LogRequestHttp.objects.create(
            url=url,
            metodo_http=metodo,
            processo_id=processo_id,
            resposta_raw=resposta,
        )

        assert log.url == url
        assert log.metodo_http == metodo
        assert log.processo_id == processo_id
        assert log.resposta_raw == resposta

    def test_log_request_http_str_representation(self):
        """Testa a representação string do model."""
        log = LogRequestHttp.objects.create(
            url="https://api.example.com/endpoint",
            metodo_http="POST",
            processo_id=123,
            resposta_raw='{"status": "ok"}',
        )

        str_repr = str(log)
        assert "Log" in str_repr
        assert "POST" in str_repr
        assert "https://api.example.com/endpoint" in str_repr
        assert "123" in str_repr

    def test_log_request_http_str_representation_sem_processo_id(self):
        """Testa a representação string quando não há processo_id."""
        log = LogRequestHttp.objects.create(
            url="https://api.example.com/endpoint",
            metodo_http="GET",
            resposta_raw='{"status": "ok"}',
        )

        str_repr = str(log)
        assert "Log" in str_repr
        assert "N/A" in str_repr

    def test_log_request_http_ordering(self):
        """Testa que o ordering está configurado corretamente."""
        log1 = LogRequestHttp.objects.create(
            url="https://api.example.com/endpoint1",
            metodo_http="POST",
            resposta_raw="response1",
        )

        import time

        time.sleep(0.01)

        log2 = LogRequestHttp.objects.create(
            url="https://api.example.com/endpoint2",
            metodo_http="GET",
            resposta_raw="response2",
        )

        logs = LogRequestHttp.objects.all()
        assert logs[0] == log2
        assert logs[1] == log1

    def test_log_request_http_campos_opcionais(self):
        """Testa que processo_id pode ser None."""
        log = LogRequestHttp.objects.create(
            url="https://api.example.com/endpoint",
            metodo_http="POST",
            resposta_raw='{"status": "ok"}',
        )

        assert log.processo_id is None

    def test_log_request_http_meta_options(self):
        """Testa as opções Meta do model."""
        assert LogRequestHttp._meta.db_table == "log_request_http"
        assert LogRequestHttp._meta.verbose_name == "Log de requisição HTTP"
        assert (
            LogRequestHttp._meta.verbose_name_plural
            == "Log de requisição HTTP"
        )

    def test_log_request_http_url_max_length(self):
        """Testa que a URL pode ter até 500 caracteres."""
        long_url = "https://api.example.com/" + "a" * 470
        log = LogRequestHttp.objects.create(
            url=long_url,
            metodo_http="POST",
            resposta_raw="response",
        )

        assert len(log.url) <= 500

    def test_log_request_http_metodo_http_max_length(self):
        """Testa que metodo_http pode ter até 10 caracteres."""
        log = LogRequestHttp.objects.create(
            url="https://api.example.com/endpoint",
            metodo_http="POST",
            resposta_raw="response",
        )

        assert len(log.metodo_http) <= 10

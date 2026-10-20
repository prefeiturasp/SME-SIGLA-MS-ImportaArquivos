"""Testes de mascarar_headers das chamadas HTTP."""

from django.test import override_settings
from importa_arquivos.services.http_log import mascarar_headers


@override_settings(API_KEY_HEADER="X-API-Key")
def test_mascarar_headers_deixa_tres_caracteres_na_api_key():
    """Mascara só o header configurado em API_KEY_HEADER."""
    headers = {
        "Accept": "application/json",
        "X-API-Key": "api-key-agenda",
    }
    mascarados = mascarar_headers(headers)
    assert mascarados == {
        "Accept": "application/json",
        "X-API-Key": "api****",
    }
    assert headers["X-API-Key"] == "api-key-agenda"


@override_settings(API_KEY_HEADER="X-API-Key")
def test_mascarar_headers_ignora_outro_nome_de_header():
    """Não mascara header com nome diferente de API_KEY_HEADER."""
    headers = {"X-Api-Key": "api-key-agenda", "Accept": "application/json"}
    assert mascarar_headers(headers) == headers

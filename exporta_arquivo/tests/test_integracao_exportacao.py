"""
Teste de integração opcional: create de candidatos processo com mock apenas da API externa.
Fluxo real: view → serializer → executar_exportacao → exportar_candidatos_processo → formatar_arquivo.
Só requests.get (API Candidatos) é mockado; service, formatter e view rodam de verdade.
Garante que o pipeline não quebra.
"""
import uuid
from unittest.mock import patch, MagicMock

import pytest

from exporta_arquivo.models import ExportacaoCandidatosProcesso


pytestmark = [pytest.mark.django_db, pytest.mark.urls("exporta_arquivo.tests.urls")]


def _uuid():
    return str(uuid.uuid4())


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


def _resposta_habilitados_api():
    """Payload mínimo que a API de habilitados pode retornar e o service mapeia."""
    return [
        {
            "candidato": {
                "cpf": "12345678900",
                "nome": "Candidato Teste",
                "data_nascimento": "1990-05-15T00:00:00",
            },
            "codigo_cargo": 10,
            "ranking_escolha": 1,
            "classificacao": 5,
        },
    ]


class TestIntegracaoCreateCandidatosProcesso:
    """Create candidatos processo: mock só da API externa; resto do fluxo real."""

    URL = "/api/v1/exportacao/candidatos-processo/"

    def test_create_mockando_apenas_api_externa_retorna_200_e_arquivo_txt(self, api_client):
        """
        POST create com payload válido; mock de requests.get (API Candidatos) retorna habilitados.
        Service exportar_candidatos_processo e formatar_arquivo_candidatos_processo rodam de verdade.
        Verifica: 200, Content-Type text/plain, registro com conteudo_arquivo e nome_arquivo, conteúdo com pipe.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _resposta_habilitados_api()

        with patch("exporta_arquivo.services.api_candidatos.requests.get", return_value=mock_response):
            response = api_client.post(
                self.URL,
                {
                    "processo_uuid": _uuid(),
                    "cargo_uuid": _uuid(),
                    "cargo_codigo": 10,
                    "processo_nome": "Processo Integração",
                    "cargo_nome": "Cargo Teste",
                },
                format="json",
            )

        assert response.status_code == 200
        assert "text/plain" in response.get("Content-Type", "")
        assert "attachment" in response.get("Content-Disposition", "")
        assert "candidatos_processo" in response.get("Content-Disposition", "")

        registro = ExportacaoCandidatosProcesso.objects.order_by("-criado_em").first()
        assert registro is not None
        assert registro.conteudo_arquivo
        assert registro.nome_arquivo.startswith("candidatos_processo_")
        assert registro.nome_arquivo.endswith(".txt")
        assert "|" in registro.conteudo_arquivo
        assert "12345678900" in registro.conteudo_arquivo
        assert "Candidato Teste" in registro.conteudo_arquivo

        mock_response.json.assert_called_once()

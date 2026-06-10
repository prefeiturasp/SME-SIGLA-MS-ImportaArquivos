"""Teste de integração opcional: gerar_arquivo de candidatos processo com mock.

apenas da API externa.
Fluxo real: serializer → gerar_arquivo → exportar_candidatos_processo →
formatar_arquivo.
Só requests.get (API Candidatos) é mockado; service, formatter e view rodam de
verdade.
Garante que o pipeline não quebra.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from exporta_arquivo.serializers import ExportacaoCandidatosProcessoCreateSerializer
from exporta_arquivo.views.exportacao_candidatos_processo import (
    ExportacaoCandidatosProcessoViewSet,
)

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls("exporta_arquivo.tests.urls"),
]


def _uuid() -> Any:
    """Uuid."""
    return str(uuid.uuid4())


def _resposta_habilitados_api() -> Any:
    """Payload mínimo que a API de habilitados pode retornar e o service."""
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
        }
    ]


class TestIntegracaoCreateCandidatosProcesso:
    """gerar_arquivo candidatos processo: mock só da API externa; resto real."""

    def test_create_mockando_apenas_api_externa_retorna_200_e_arquivo_txt(
        self,
    ) -> Any:
        """Verifica gerar_arquivo mockando apenas api externa persiste arquivo txt."""
        concurso_uuid = _uuid()
        mock_concursos = MagicMock()
        mock_concursos.status_code = 200
        mock_concursos.json.return_value = {
            "codigo": 10,
            "criado_em": "2024-01-01T00:00:00",
        }
        mock_candidatos = MagicMock()
        mock_candidatos.status_code = 200
        mock_candidatos.json.return_value = _resposta_habilitados_api()
        payload = {
            "processo_uuid": _uuid(),
            "cargo_uuid": _uuid(),
            "cargo_codigo": 10,
            "concurso_uuid": concurso_uuid,
            "processo_nome": "Processo Integração",
            "cargo_nome": "Cargo Teste",
        }
        serializer = ExportacaoCandidatosProcessoCreateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        registro = serializer.save()
        viewset = ExportacaoCandidatosProcessoViewSet()

        def fake_get(url: Any, *args: Any, **kwargs: Any) -> Any:
            """Fake get."""
            if "concursos" in url:
                return mock_concursos
            return mock_candidatos

        with patch(
            "sigla_sdk.http.api_client.http_client.get", side_effect=fake_get
        ):
            viewset.gerar_arquivo(registro)
        registro.refresh_from_db()
        assert registro.conteudo_arquivo
        assert registro.nome_arquivo.startswith("candidatos_processo_")  # type: ignore[union-attr]
        assert registro.nome_arquivo.endswith(".txt")  # type: ignore[union-attr]
        assert "|" in registro.conteudo_arquivo
        assert "12345678900" in registro.conteudo_arquivo
        assert "Candidato Teste" in registro.conteudo_arquivo
        mock_candidatos.json.assert_called_once()

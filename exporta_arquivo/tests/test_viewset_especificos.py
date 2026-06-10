"""Testes específicos de cada ViewSet concreta: qual service é chamado e.

do arquivo.
O restante (list, create com exceções, download, get_serializer_class) já está
na base.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest

from exporta_arquivo.models import (
    ExportacaoCandidatosProcesso,
    ExportacaoVagasProcesso,
    ExportacaoVagasSigpec,
)

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls("exporta_arquivo.tests.urls"),
]


def _uuid() -> Any:
    """Uuid."""
    return str(uuid.uuid4())


@pytest.fixture
def api_client() -> Any:
    """Api client."""
    from rest_framework.test import APIClient

    return APIClient()


class TestExportacaoCandidatosProcessoViewSetEspecifico:
    """Create: mock exportar_candidatos_processo e."""

    URL = "/api/v1/exportacao/candidatos-processo/"

    def test_create_com_mocks_persiste_conteudo_e_nome_arquivo_prefixo_candidatos_processo(  # noqa: E501
        self, api_client: Any
    ) -> None:
        """Verifica create com mocks persiste conteudo e nome arquivo prefixo."""
        conteudo_esperado = "conteudo|pipe|formatado\n"
        with patch(
            "exporta_arquivo.views.exportacao_candidatos_processo.exportar_candidatos_processo",
            return_value=conteudo_esperado,
        ):
            response = api_client.post(
                self.URL,
                {
                    "processo_uuid": _uuid(),
                    "cargo_uuid": _uuid(),
                    "cargo_codigo": 10,
                    "processo_nome": "Proc",
                    "cargo_nome": "Cargo X",
                },
                format="json",
            )
        assert response.status_code == 200
        assert "text/plain" in response.get("Content-Type", "")
        registro = ExportacaoCandidatosProcesso.objects.order_by(
            "-criado_em"
        ).first()
        assert registro is not None
        assert registro.conteudo_arquivo == conteudo_esperado
        assert registro.nome_arquivo.startswith("candidatos_processo_")  # type: ignore[union-attr]
        assert registro.nome_arquivo.endswith(".txt")  # type: ignore[union-attr]
        assert "attachment" in response.get("Content-Disposition", "")
        assert "candidatos_processo" in response.get("Content-Disposition", "")


class TestExportacaoVagasProcessoViewSetEspecifico:
    """Create: mock buscar_vagas_escolas e formatar_arquivo_vagas_processo;."""

    URL = "/api/v1/exportacao/vagas-processo/"

    def test_create_com_mocks_persiste_conteudo_e_nome_exportacao_vagas_processo(  # noqa: E501
        self, api_client: Any
    ) -> None:
        """Verifica create com mocks persiste conteudo e nome exportacao vagas."""
        vagas_escolas = [
            {
                "codigo_eol": "EOL1",
                "vagas_definitivas": 2,
                "vagas_precarias": 1,
            }
        ]
        conteudo_esperado = "100|EOL1|2|1\n"
        with (
            patch(
                "exporta_arquivo.views.exportacao_vagas_processo.buscar_vagas_escolas",
                return_value=vagas_escolas,
            ),
            patch(
                "exporta_arquivo.views.exportacao_vagas_processo.formatar_arquivo_vagas_processo",
                return_value=conteudo_esperado,
            ),
        ):
            response = api_client.post(
                self.URL,
                {
                    "processo_uuid": _uuid(),
                    "cargo_uuid": _uuid(),
                    "cargo_codigo": 100,
                    "processo_nome": "Processo",
                    "cargo_nome": "Cargo",
                },
                format="json",
            )
        assert response.status_code == 200
        assert "text/plain" in response.get("Content-Type", "")
        registro = ExportacaoVagasProcesso.objects.order_by(
            "-criado_em"
        ).first()
        assert registro is not None
        assert registro.conteudo_arquivo == conteudo_esperado
        assert registro.nome_arquivo.startswith("exportacao-vagas-processo-")  # type: ignore[union-attr]
        assert registro.nome_arquivo.endswith(".txt")  # type: ignore[union-attr]
        assert "exportacao-vagas-processo" in response.get(
            "Content-Disposition", ""
        )


class TestExportacaoVagasSigpecViewSetEspecifico:
    """Create: mock buscar_vagas_escolas e formatar_arquivo_sigpec; nome."""

    URL = "/api/v1/exportacao/vagas-sigpec/"

    def test_create_com_mocks_persiste_conteudo_sigpec_e_nome_exportacao_vagas_sigpec(  # noqa: E501
        self, api_client: Any
    ) -> None:
        """Verifica create com mocks persiste conteudo sigpec e nome."""
        vagas_escolas = [
            {
                "codigo_integracao": "SETOR01",
                "vagas_definitivas": 3,
                "vagas_precarias": 0,
            }
        ]
        conteudo_sigpec = (
            "@TABELA=[C_ERGON][PMSP_VAGAS_SME][1.0]\nSETOR01;3;0;\n"
        )
        with (
            patch(
                "exporta_arquivo.views.exportacao_vagas_sigpec.buscar_vagas_escolas",
                return_value=vagas_escolas,
            ),
            patch(
                "exporta_arquivo.views.exportacao_vagas_sigpec.formatar_arquivo_sigpec",
                return_value=conteudo_sigpec,
            ),
        ):
            response = api_client.post(
                self.URL,
                {
                    "processo_uuid": _uuid(),
                    "cargo_uuid": _uuid(),
                    "cargo_codigo": 200,
                    "processo_nome": "SIGPEC",
                    "cargo_nome": "Cargo",
                },
                format="json",
            )
        assert response.status_code == 200
        assert "text/plain" in response.get("Content-Type", "")
        registro = ExportacaoVagasSigpec.objects.order_by("-criado_em").first()
        assert registro is not None
        assert registro.conteudo_arquivo == conteudo_sigpec
        assert "@TABELA=" in registro.conteudo_arquivo
        assert "SETOR01;3;0;" in registro.conteudo_arquivo
        assert registro.nome_arquivo.startswith("exportacao-vagas-sigpec-")  # type: ignore[union-attr]
        assert registro.nome_arquivo.endswith(".txt")  # type: ignore[union-attr]
        assert "exportacao-vagas-sigpec" in response.get(
            "Content-Disposition", ""
        )

"""Módulo tests/services/conftest."""

from __future__ import annotations

from typing import Any

import pytest

from importa_arquivos.models import LayoutArquivoImportacao

pytestmark = pytest.mark.django_db


@pytest.fixture
def layout_vagas() -> Any:
    """Layout vagas."""
    return LayoutArquivoImportacao.objects.create(
        tipo="VAGAS",
        estrutura=[
            {
                "coluna": "DataFechamentoModulo",
                "campo_payload": "data_fechamento_modulo",
            }
        ],
    )


@pytest.fixture
def layout_habilitados() -> Any:
    """Layout habilitados."""
    return LayoutArquivoImportacao.objects.create(
        tipo="HABILITADOS",
        estrutura=[{"coluna": "CPF", "campo_payload": "cpf"}],
    )

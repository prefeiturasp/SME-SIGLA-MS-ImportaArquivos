"""Módulo tests/conftest."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from importa_arquivos.models import ImportacaoArquivoVagas


@pytest.fixture
def api_client() -> Any:
    """Fixture para criar um cliente API de teste."""
    return APIClient()


@pytest.fixture
def fake_uuid() -> Any:
    """Fixture para gerar UUIDs falsos para testes."""
    return uuid.uuid4()


@pytest.fixture
def cria_vagas() -> Any:
    """Cria vagas."""

    def _cria(pares_nome_status: Any) -> Any:
        """Cria."""
        objetos = []
        for nome, status in pares_nome_status:
            objetos.append(
                ImportacaoArquivoVagas.objects.create(
                    nome_arquivo=nome,
                    arquivo=SimpleUploadedFile(nome, b"content"),
                    status=status,
                )
            )
        return objetos

    return _cria

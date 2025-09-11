import pytest
from rest_framework.test import APIClient
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile
from importa_arquivos.models import ImportacaoArquivoVagas


@pytest.fixture
def api_client():
    """
    Fixture para criar um cliente API de teste.
    """
    return APIClient()


@pytest.fixture
def fake_uuid():
    """
    Fixture para gerar UUIDs falsos para testes.
    """
    return uuid.uuid4()


@pytest.fixture
def cria_vagas():
    def _cria(pares_nome_status):
        objetos = []
        for nome, status in pares_nome_status:
            objetos.append(
                ImportacaoArquivoVagas.objects.create(
                    nome_arquivo=nome,
                    arquivo=SimpleUploadedFile(nome, b'content'),
                    status=status,
                )
            )
        return objetos
    return _cria

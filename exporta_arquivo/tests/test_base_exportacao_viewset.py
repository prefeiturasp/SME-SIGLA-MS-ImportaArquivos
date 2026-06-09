"""Testes do comportamento da BaseExportacaoViewSet uma vez, via.

ExportacaoVagasSigpecViewSet como proxy.
Cobre: list (com/sem query params), create (sucesso e exceções), download,
get_serializer_class.
Usa ROOT_URLCONF mínimo (exporta_arquivo.tests.urls) para não carregar
importa_arquivos.
"""
from __future__ import annotations
from typing import Any
import uuid
from unittest.mock import patch
import pytest
from django.http import HttpResponse
from exporta_arquivo.models import ExportacaoVagasSigpec
from exporta_arquivo.services.exceptions import ExportacaoBadRequestException, ExportacaoNotFoundException, ExportacaoServiceUnavailableException
pytestmark = [pytest.mark.django_db, pytest.mark.urls('exporta_arquivo.tests.urls')]
LIST_URL = '/api/v1/exportacao/vagas-sigpec/'

def _uuid() -> Any:
    """Executa  uuid."""
    return str(uuid.uuid4())

@pytest.fixture
def api_client() -> Any:
    """Executa api client."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def registro_com_arquivo() -> Any:
    """
    Registro no banco com conteudo_arquivo e nome_arquivo preenchidos (para
    download).
    """
    return ExportacaoVagasSigpec.objects.create(processo_uuid=uuid.uuid4(), cargo_uuid=uuid.uuid4(), cargo_codigo=100, conteudo_arquivo='conteudo;1;0;\n', nome_arquivo='exportacao-vagas-sigpec.txt')

class TestBaseExportacaoList:
    """list: sem params (paginado), com params inválidos (400), com params válidos.

    (arquivo).
    """

    def test_list_sem_query_params_retorna_200_paginado(self, api_client: Any) -> None:
        """GET list sem query params → 200 e resposta paginada."""
        ExportacaoVagasSigpec.objects.create(processo_uuid=uuid.uuid4(), cargo_uuid=uuid.uuid4(), cargo_codigo=1)
        response = api_client.get(LIST_URL)
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert 'count' in data
        assert 'page' in data
        assert 'page_size' in data or 'links' in data

    def test_list_com_processo_e_cargo_uuid_sem_cargo_codigo_retorna_400(self, api_client: Any) -> None:
        """GET list com processo_uuid e cargo_uuid mas sem cargo_codigo → 400 e.

        mensagem sobre cargo_codigo na query.
        """
        response = api_client.get(LIST_URL, {'processo_uuid': _uuid(), 'cargo_uuid': _uuid()})
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'cargo_codigo' in data['detail'].lower()
        assert 'query' in data['detail'].lower() or 'envie' in data['detail'].lower()

    def test_list_com_cargo_codigo_nao_numerico_retorna_400(self, api_client: Any) -> None:
        """GET list com cargo_codigo não numérico → 400 e mensagem cargo_codigo.

        numérico.
        """
        response = api_client.get(LIST_URL, {'processo_uuid': _uuid(), 'cargo_uuid': _uuid(), 'cargo_codigo': 'abc'})
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'numérico' in data['detail'] or 'numerico' in data['detail'].lower()

    def test_list_com_params_validos_retorna_arquivo(self, api_client: Any) -> None:
        """GET list com processo_uuid, cargo_uuid e cargo_codigo válidos → 200 e.

        resposta de arquivo (mock).
        """
        p, c = (_uuid(), _uuid())
        mock_response = HttpResponse(b'conteudo mock', content_type='text/plain; charset=utf-8')
        mock_response['Content-Disposition'] = 'attachment; filename="arquivo.txt"'
        with patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.gerar_arquivo', return_value=mock_response):
            response = api_client.get(LIST_URL, {'processo_uuid': p, 'cargo_uuid': c, 'cargo_codigo': '200'})
        assert response.status_code == 200
        assert 'attachment' in response.get('Content-Disposition', '')
        assert 'text/plain' in response.get('Content-Type', '')

class TestBaseExportacaoGetSerializerClass:
    """get_serializer_class: create usa create_serializer_class; list/retrieve usa.

    list_serializer_class.
    """

    def test_post_create_usa_create_serializer(self, api_client: Any) -> None:
        """POST (create) usa create_serializer_class (valida campos do create)."""
        with patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.executar_exportacao'), patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.gerar_arquivo', return_value=HttpResponse(b'x', content_type='text/plain')):
            response = api_client.post(LIST_URL, {'processo_uuid': _uuid(), 'cargo_uuid': _uuid(), 'cargo_codigo': 1}, format='json')
        assert response.status_code == 200
        from exporta_arquivo.serializers.exportacao_vagas_sigpec import ExportacaoVagasSigpecCreateSerializer
        assert ExportacaoVagasSigpecCreateSerializer.Meta.fields

    def test_get_list_usa_list_serializer(self, api_client: Any) -> None:
        """GET list usa list_serializer_class (resposta com uuid, criado_em,.

        etc.).
        """
        ExportacaoVagasSigpec.objects.create(processo_uuid=uuid.uuid4(), cargo_uuid=uuid.uuid4(), cargo_codigo=1)
        response = api_client.get(LIST_URL)
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert len(data['results']) >= 1
        from exporta_arquivo.serializers.exportacao_vagas_sigpec import ExportacaoVagasSigpecListSerializer
        list_fields = set(ExportacaoVagasSigpecListSerializer.Meta.fields)
        for key in list_fields:
            assert key in data['results'][0]

class TestBaseExportacaoCreate:
    """create: dados válidos + mock executar_exportacao → 200 e arquivo; exceções.

    → 400/404/502.
    """

    def test_create_com_dados_validos_mock_executar_retorna_200_arquivo(self, api_client: Any) -> None:
        """POST com dados válidos e mock de executar_exportacao → 200 e resposta.

        de arquivo.
        """
        with patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.executar_exportacao'), patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.gerar_arquivo', return_value=HttpResponse(b'arquivo gerado', content_type='text/plain; charset=utf-8')):
            response = api_client.post(LIST_URL, {'processo_uuid': _uuid(), 'cargo_uuid': _uuid(), 'cargo_codigo': 10}, format='json')
        assert response.status_code == 200
        assert 'text/plain' in response.get('Content-Type', '')

    def test_create_executar_levanta_bad_request_retorna_400(self, api_client: Any) -> None:
        """executar_exportacao levanta ExportacaoBadRequestException → 400 e.

        detail.
        """
        with patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.executar_exportacao', side_effect=ExportacaoBadRequestException(mensagem='cargo_codigo inválido.')):
            response = api_client.post(LIST_URL, {'processo_uuid': _uuid(), 'cargo_uuid': _uuid(), 'cargo_codigo': 99}, format='json')
        assert response.status_code == 400
        data = response.json()
        assert 'mensagem' in data
        assert 'cargo_codigo' in data['mensagem'].lower() or 'inválido' in data['mensagem'].lower()

    def test_create_executar_levanta_not_found_retorna_404(self, api_client: Any) -> None:
        """executar_exportacao levanta ExportacaoNotFoundException → 404 e detail."""
        with patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.executar_exportacao', side_effect=ExportacaoNotFoundException(mensagem='Processo não encontrado.')):
            response = api_client.post(LIST_URL, {'processo_uuid': _uuid(), 'cargo_uuid': _uuid(), 'cargo_codigo': 99}, format='json')
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data

    def test_create_executar_levanta_service_unavailable_retorna_502(self, api_client: Any) -> None:
        """executar_exportacao levanta ExportacaoServiceUnavailableException → 502.

        e detail.
        """
        with patch('exporta_arquivo.views.exportacao_vagas_sigpec.ExportacaoVagasSigpecViewSet.executar_exportacao', side_effect=ExportacaoServiceUnavailableException(mensagem='API indisponível.')):
            response = api_client.post(LIST_URL, {'processo_uuid': _uuid(), 'cargo_uuid': _uuid(), 'cargo_codigo': 99}, format='json')
        assert response.status_code == 502
        data = response.json()
        assert 'detail' in data
        assert 'indisponível' in data['detail'] or 'detail' in data

class TestBaseExportacaoDownload:
    """download: GET /<uuid>/download/ com instance que tem conteudo e nome → 200.

    e corpo do arquivo.
    """

    def test_download_com_registro_com_arquivo_retorna_200_e_corpo(self, api_client: Any, registro_com_arquivo: Any) -> None:
        """GET /<uuid>/download/ com instance que tem conteudo_arquivo e.

        nome_arquivo → 200 e corpo.
        """
        url = f'{LIST_URL.rstrip('/')}/{str(registro_com_arquivo.uuid)}/download/'
        response = api_client.get(url)
        assert response.status_code == 200
        assert b'conteudo' in response.content
        assert 'attachment' in response.get('Content-Disposition', '')
        assert registro_com_arquivo.nome_arquivo in response.get('Content-Disposition', '')

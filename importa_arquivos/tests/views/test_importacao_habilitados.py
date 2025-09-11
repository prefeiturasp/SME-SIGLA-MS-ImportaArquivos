import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock


pytestmark = pytest.mark.django_db


def test_importacao_habilitados_create_success(api_client, settings):
    settings.CANDIDATOS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar, \
         patch('importa_arquivos.views.importacao_habilitados.ApiCandidatosService') as mock_api:
        mock_validar.return_value = (
            [{'Inscricao': '123', 'Nome': 'Joao'}],
            [{'coluna': 'Inscricao', 'campo_payload': 'codigo_inscricao'}]
        )
        mock_api.return_value.enviar_habilitados.return_value = Mock()

        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'concurso_uuid': '11111111-1111-1111-1111-111111111111',
            'concurso_nome': 'Concurso X',
            'tipo': 'HABILITADOS',
        }, format='multipart')

        assert resp.status_code in (200, 201)
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_habilitados.assert_called_once()


def test_importacao_habilitados_cria_arquivo_com_validation_error(api_client):
    arquivo = SimpleUploadedFile('h.csv', b'invalid', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar:
        mock_validar.side_effect = ValueError('erro de layout')

        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'concurso_uuid': '11111111-1111-1111-1111-111111111111',
            'concurso_nome': 'Concurso X',
            'tipo': 'HABILITADOS',
        }, format='multipart')

        assert resp.status_code == 400


def test_importacao_habilitados_cria_arquivo_sem_arquivo(api_client):
    url = reverse('importacao-arquivo-habilitados-list')
    resp = api_client.post(url, {
        'concurso_uuid': '11111111-1111-1111-1111-111111111111',
        'concurso_nome': 'Concurso X',
        'tipo': 'HABILITADOS',
    }, format='multipart')
    assert resp.status_code == 400


def test_importacao_habilitados_cria_arquivo_com_exception(api_client):
    arquivo = SimpleUploadedFile('h.csv', b'invalid', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar:
        mock_validar.side_effect = Exception('boom')

        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'concurso_uuid': '11111111-1111-1111-1111-111111111111',
            'concurso_nome': 'Concurso X',
            'tipo': 'HABILITADOS',
        }, format='multipart')

        assert resp.status_code == 400


def test_importacao_habilitados_envio_api_exception(api_client, settings):
    settings.CANDIDATOS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar, \
         patch('importa_arquivos.views.importacao_habilitados.ApiCandidatosService') as mock_api:
        mock_validar.return_value = (
            [{'Inscricao': '123', 'Nome': 'Joao'}],
            [{'coluna': 'Inscricao', 'campo_payload': 'codigo_inscricao'}]
        )
        mock_api.return_value.enviar_habilitados.side_effect = Exception('api fail')

        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'concurso_uuid': '11111111-1111-1111-1111-111111111111',
            'concurso_nome': 'Concurso X',
            'tipo': 'HABILITADOS',
        }, format='multipart')

        # Mesmo com falha no envio à API externa, a criação deve ter sucesso
        assert resp.status_code in (200, 201)
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_habilitados.assert_called_once()

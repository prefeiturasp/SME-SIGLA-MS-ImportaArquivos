import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock

pytestmark = pytest.mark.django_db


def test_importacao_vagas_create_success(api_client, settings):
    settings.ESCOLHAS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
         patch('importa_arquivos.views.importacao_vagas.ApiVagasService') as mock_api:
        mock_validar.return_value = (
            [{'DataFechamentoModulo': '05/09/2025'}],
            [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
        )
        mock_api.return_value.enviar_vagas.return_value = Mock()

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code in (200, 201)
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_vagas.assert_called_once()


def test_importacao_vagas_create_validation_error(api_client):
    arquivo = SimpleUploadedFile('v.csv', b'invalid', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar:
        mock_validar.side_effect = ValueError('erro de layout') 

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code == 400


def test_importacao_vagas_create_unexpected_exception(api_client):
    arquivo = SimpleUploadedFile('v.csv', b'invalid', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar:
        mock_validar.side_effect = Exception('boom')

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code == 400
        assert resp.data.get('detail') == 'Erro ao validar CSV.'


def test_importacao_vagas_envio_api_exception(api_client, settings):
    settings.ESCOLHAS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
         patch('importa_arquivos.views.importacao_vagas.ApiVagasService') as mock_api:
        mock_validar.return_value = (
            [{'DataFechamentoModulo': '05/09/2025'}],
            [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
        )
        mock_api.return_value.enviar_vagas.side_effect = Exception('api fail')

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code in (200, 201)
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_vagas.assert_called_once()


def test_importacao_vagas_list_success(api_client, cria_vagas):
    cria_vagas([
        ('teste1.csv', 'PENDENTE'),
        ('teste2.csv', 'PROCESSADO'),
    ])

    url = reverse('importacao-arquivo-vagas-list')
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert 'results' in resp.data
    assert len(resp.data['results']) == 2
    assert resp.data['results'][0]['nome_arquivo'] in ['teste1.csv', 'teste2.csv']


def test_importacao_vagas_retrieve_success(api_client, cria_vagas):
    objs = cria_vagas([
        ('teste.csv', 'PENDENTE'),
    ])
    obj = objs[0]

    url = reverse('importacao-arquivo-vagas-detail', kwargs={'pk': obj.pk})
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert resp.data['nome_arquivo'] == 'teste.csv'
    assert resp.data['status'] == 'PENDENTE'
    assert 'uuid' in resp.data


import pytest
from django.urls import reverse
from importa_arquivos.models.layout import LayoutArquivoImportacao
from importa_arquivos.models.base import CHOICES_TIPO_IMPORTACAO_ARQUIVO

pytestmark = pytest.mark.django_db


def test_layout_list_empty(api_client):
    url = reverse('layout-arquivo-list')
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert resp.data['count'] == 0


def test_layout_create_and_list(api_client):
    url = reverse('layout-arquivo-list')
    payload = {
        'nome': 'Layout Vagas',
        'tipo': 'VAGAS',
        'estrutura': [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}],
    }
    resp_create = api_client.post(url, payload, format='json')
    assert resp_create.status_code in (200, 201)

    resp_list = api_client.get(url)
    assert resp_list.status_code == 200
    assert resp_list.data['count'] == 1

    obj = LayoutArquivoImportacao.objects.first()
    assert obj is not None
    assert obj.tipo == 'VAGAS'


def test_download_sem_tipo_retorna_400(api_client):
    url = reverse('layout-arquivo-download')
    resp = api_client.get(url)
    assert resp.status_code == 400
    assert 'tipo' in (resp.json().get('detail') or '').lower()


def test_download_layout_nao_encontrado_404(api_client):
    url = reverse('layout-arquivo-download')
    resp = api_client.get(url, {'tipo': 'VAGAS'})
    assert resp.status_code == 404


def test_download_vagas_csv_delimitador_ponto_virgula(api_client):
    LayoutArquivoImportacao.objects.create(
        tipo='VAGAS',
        estrutura=[
            {'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'},
            {'coluna': 'DATA', 'campo_payload': 'data'}
        ]
    )
    url = reverse('layout-arquivo-download')
    resp = api_client.get(url, {'tipo': 'VAGAS'})
    assert resp.status_code == 200
    assert resp['Content-Type'].startswith('text/csv')
    assert 'attachment; filename="layout_vagas.csv"' in resp['Content-Disposition']
    content = resp.content.decode('utf-8')
    assert 'DataFechamentoModulo;DATA' in content


def test_download_habilitados_csv_delimitador_virgula(api_client):
    LayoutArquivoImportacao.objects.create(
        tipo='HABILITADOS',
        estrutura=[
            {'coluna': 'CPF', 'campo_payload': 'cpf'},
            {'coluna': 'NOME', 'campo_payload': 'nome'}
        ]
    )
    url = reverse('layout-arquivo-download')
    resp = api_client.get(url, {'tipo': 'HABILITADOS'})
    assert resp.status_code == 200
    assert resp['Content-Type'].startswith('text/csv')
    assert 'attachment; filename="layout_habilitados.csv"' in resp['Content-Disposition']
    content = resp.content.decode('utf-8')
    assert 'CPF,NOME' in content


def test_download_estrutura_vazia_sem_cabecalho(api_client):
    LayoutArquivoImportacao.objects.create(
        tipo='VAGAS',
        estrutura=[]
    )
    url = reverse('layout-arquivo-download')
    resp = api_client.get(url, {'tipo': 'VAGAS'})
    assert resp.status_code == 200
    content = resp.content.decode('utf-8')
    assert content == ''

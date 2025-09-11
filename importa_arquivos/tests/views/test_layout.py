import pytest
from django.urls import reverse
from importa_arquivos.models.layout import LayoutArquivoImportacao

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

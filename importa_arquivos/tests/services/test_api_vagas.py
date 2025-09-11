import pytest
from unittest.mock import patch, Mock

from importa_arquivos.services.api_vagas import ApiVagasService


def test_api_vagas_transformacao_converte_data():
    svc = ApiVagasService(base_url='https://api.exemplo')
    registros = [
        {'DataFechamentoModulo': '07/01/2025', 'OutraColuna': 'x'},
    ]
    estrutura = [
        {'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'},
        {'coluna': 'OutraColuna', 'campo_payload': 'outra_coluna'},
    ]

    dados = svc._transformar_registros(registros, estrutura)
    assert dados[0]['data_fechamento_modulo'] == '2025-01-07'
    assert dados[0]['outra_coluna'] == 'x'


@pytest.mark.django_db
def test_api_vagas_enviar_payload_ok(settings):
    settings.CANDIDATOS_API_URL = 'https://api.exemplo'
    svc = ApiVagasService(base_url=settings.CANDIDATOS_API_URL)

    registros = [{'DataFechamentoModulo': '05/09/2025'}]
    estrutura = [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]

    with patch('importa_arquivos.services.api_vagas.requests.post') as mock_post:
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        resp = svc.enviar_vagas(registros=registros, estrutura=estrutura)
        assert resp is mock_resp
        args, kwargs = mock_post.call_args
        assert args[0].endswith('/api/v1/vagas-escolas')
        assert kwargs['json']['vagas'][0]['data_fechamento_modulo'] == '2025-09-05' 
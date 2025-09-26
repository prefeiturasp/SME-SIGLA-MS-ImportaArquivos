import pytest
from unittest.mock import patch, Mock
from requests import RequestException

from importa_arquivos.models import ImportacaoArquivoVagas, ImportacaoErro
from importa_arquivos.services.api_vagas import ApiVagasService


pytestmark = pytest.mark.django_db


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
    assert dados[0]['data_fechamento_modulo'] == '07/01/2025'
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
        assert args[0].endswith('/api/v1/vagas-escolas/')
        assert kwargs['json']['vagas'][0]['data_fechamento_modulo'] == '05/09/2025' 


def test_api_vagas_cria_erro_quando_request_falha():
    obj = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='v.csv', arquivo='importacoes/v.csv', tipo='VAGAS'
    )

    service = ApiVagasService(base_url='http://example.com')

    with patch('importa_arquivos.services.api_vagas.requests.post', side_effect=RequestException('boom')):
        with pytest.raises(RequestException):
            service.enviar_vagas(
                registros=[{'A': '1'}],
                estrutura=[{'coluna': 'A', 'campo_payload': 'a'}],
                importacao_obj=obj,
            )

    assert ImportacaoErro.objects.filter(object_id=obj.uuid).exists()


def test_transformar_registros_converte_data_sucesso():
    service = ApiVagasService()
    registros = [{'DATA': ' 05/09/2025 '}]  # com espaços
    estrutura = [{'coluna': 'DATA', 'campo_payload': 'data'}]

    out = service._transformar_registros(registros, estrutura)
    assert out == [{'data': '2025-09-05'}]


def test_transformar_registros_mantem_valor_quando_data_invalida():
    service = ApiVagasService()
    registros = [{'DATA': 'valor_invalido'}]
    estrutura = [{'coluna': 'DATA', 'campo_payload': 'data'}]

    out = service._transformar_registros(registros, estrutura)
    assert out == [{'data': 'valor_invalido'}]


def test_api_vagas_nao_quebra_quando_registrar_erro_falha():
    obj = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='v2.csv', arquivo='importacoes/v2.csv', tipo='VAGAS'
    )
    service = ApiVagasService(base_url='http://example.com')

    with patch('importa_arquivos.services.api_vagas.requests.post', side_effect=RequestException('boom')):
        with patch('importa_arquivos.services.api_vagas.registrar_erro', side_effect=RuntimeError('fail-log')) as mock_reg:
            with pytest.raises(RequestException):
                service.enviar_vagas(
                    registros=[{'A': '1'}],
                    estrutura=[{'coluna': 'A', 'campo_payload': 'a'}],
                    importacao_obj=obj,
                )
            assert mock_reg.called

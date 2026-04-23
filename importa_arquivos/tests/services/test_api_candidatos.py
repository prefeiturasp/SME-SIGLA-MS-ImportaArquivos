import pytest
from unittest.mock import patch, Mock
from django.core.files.base import ContentFile
from importa_arquivos.models import ImportacaoArquivoHabilitado, ImportacaoErro
from importa_arquivos.services.api_candidatos import ApiCandidatosService
from importa_arquivos.services.exceptions import ApiCandidatosException
from requests import RequestException


pytestmark = pytest.mark.django_db


def test_api_candidatos_transformacao_basica():
    svc = ApiCandidatosService(base_url='https://api.exemplo')
    registros = [
        {'Inscricao': '123', 'Nome': 'Joao', 'Ignorada': 'x'},
    ]
    estrutura = [
        {'coluna': 'Inscricao', 'campo_payload': 'codigo_inscricao'},
        {'coluna': 'Nome', 'campo_payload': 'nome'},
        # 'Ignorada' sem mapeamento em estrutura
    ]

    dados = svc._transformar_registros(registros, estrutura)
    assert dados == [{'codigo_inscricao': '123', 'nome': 'Joao'}]


def test_api_candidatos_enviar_habilitados_payload_ok(settings):
    settings.CANDIDATOS_API_URL = 'https://api.exemplo'
    svc = ApiCandidatosService(base_url=settings.CANDIDATOS_API_URL)

    registros = [{'Inscricao': '123', 'Nome': 'Joao'}]
    estrutura = [
        {'coluna': 'Inscricao', 'campo_payload': 'codigo_inscricao'},
        {'coluna': 'Nome', 'campo_payload': 'nome'},
    ]

    with patch('sigla_sdk.http.api_client.http_client.post') as mock_post:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'ok': True}
        mock_post.return_value = mock_resp

        resp = svc.enviar_habilitados(
            registros=registros,
            estrutura=estrutura,
            concurso_uuid='11111111-1111-1111-1111-111111111111',
            concurso_nome='Concurso X',
        )

        assert resp == {'ok': True}
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        assert payload['concurso_uuid'] == '11111111-1111-1111-1111-111111111111'
        assert payload['concurso_nome'] == 'Concurso X'
        assert payload['candidatos'][0]['codigo_inscricao'] == '123'
        assert payload['candidatos'][0]['nome'] == 'Joao'


def test_api_candidatos_cria_erro_quando_request_falha():
    obj = ImportacaoArquivoHabilitado.objects.create(
        nome_arquivo='h.csv', arquivo='importacoes/h.csv', tipo='HABILITADOS',
        concurso_uuid='00000000-0000-0000-0000-000000000000', concurso_nome='Teste'
    )

    service = ApiCandidatosService(base_url='http://example.com')

    with patch('sigla_sdk.http.api_client.http_client.post', side_effect=RequestException('boom')):
        with pytest.raises(RequestException):
            service.enviar_habilitados(
                registros=[{'x': 'y'}],
                estrutura=[{'coluna': 'x', 'campo_payload': 'x'}],
                concurso_uuid=str(obj.concurso_uuid),
                concurso_nome=obj.concurso_nome,
                importacao_obj=obj,
            )

    assert ImportacaoErro.objects.filter(object_id=obj.uuid).exists()


def test_api_candidatos_levanta_excecao_especifica_quando_status_nao_for_200():
    service = ApiCandidatosService(base_url='http://example.com')

    mock_resp = Mock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {'detail': 'Erro externo', 'code': 'ERRO_EXTERNO'}
    mock_resp.text = '{"detail":"Erro externo","code":"ERRO_EXTERNO"}'

    with patch('sigla_sdk.http.api_client.http_client.post', return_value=mock_resp):
        with pytest.raises(ApiCandidatosException) as exc_info:
            service.enviar_habilitados(
                registros=[{'x': 'y'}],
                estrutura=[{'coluna': 'x', 'campo_payload': 'x'}],
                concurso_uuid='11111111-1111-1111-1111-111111111111',
                concurso_nome='Concurso X',
            )

    exc = exc_info.value
    assert exc.status_code == 400
    assert exc.mensagem == 'Falha ao enviar candidatos para API externa'
    assert 'Erro externo' in (exc.detalhes or '')

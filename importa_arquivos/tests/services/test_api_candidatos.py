import pytest
from unittest.mock import patch, Mock

from importa_arquivos.services.api_candidatos import ApiCandidatosService


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

    with patch('importa_arquivos.services.api_candidatos.requests.post') as mock_post:
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        resp = svc.enviar_habilitados(
            registros=registros,
            estrutura=estrutura,
            concurso_uuid='11111111-1111-1111-1111-111111111111',
            concurso_nome='Concurso X',
        )

        assert resp is mock_resp
        args, kwargs = mock_post.call_args
        assert args[0].endswith('/api/v1/candidatos')
        payload = kwargs['json']
        assert payload['concurso_uuid'] == '11111111-1111-1111-1111-111111111111'
        assert payload['concurso_nome'] == 'Concurso X'
        assert payload['candidatos'][0]['codigo_inscricao'] == '123'
        assert payload['candidatos'][0]['nome'] == 'Joao'

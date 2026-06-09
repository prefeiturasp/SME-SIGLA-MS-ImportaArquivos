"""Módulo tests/services/test_api_vagas."""
from __future__ import annotations
from typing import Any
from unittest.mock import Mock, patch
import pytest
from requests import RequestException
from importa_arquivos.models import ImportacaoArquivoVagas, ImportacaoErro
from importa_arquivos.services.api_escolhas import ApiEscolhasService
from importa_arquivos.services.exceptions import ApiEscolhasException, TipoUEDesabilitadoException
pytestmark = pytest.mark.django_db

def test_api_vagas_transformacao_converte_data() -> None:
    """Verifica api vagas transformacao converte data.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = ApiEscolhasService(base_url='https://api.exemplo')
    registros = [{'DataFechamentoModulo': '07/01/2025', 'OutraColuna': 'x'}]
    estrutura = [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}, {'coluna': 'OutraColuna', 'campo_payload': 'outra_coluna'}]
    dados = svc._transformar_registros(registros, estrutura)
    assert dados[0]['data_fechamento_modulo'] == '07/01/2025'
    assert dados[0]['outra_coluna'] == 'x'

@pytest.mark.django_db
def test_api_vagas_enviar_payload_ok(settings: Any) -> None:
    """Verifica api vagas enviar payload ok.
    
    Args:
        settings: Parâmetro settings da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'https://api.exemplo'
    svc = ApiEscolhasService(base_url=settings.CANDIDATOS_API_URL)
    registros = [{'DataFechamentoModulo': '05/09/2025'}]
    estrutura = [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
    with patch('sigla_sdk.http.api_client.http_client.post') as mock_post:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'ok': True}
        mock_post.return_value = mock_resp
        resp = svc.enviar_vagas(registros=registros, estrutura=estrutura)
        assert resp == {'ok': True}
        args, kwargs = mock_post.call_args
        assert args[0].endswith('/api/v1/vagas-escolas/')
        assert kwargs['json']['vagas'][0]['data_fechamento_modulo'] == '05/09/2025'

def test_api_vagas_cria_erro_quando_request_falha() -> None:
    """Verifica api vagas cria erro quando request falha.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    obj = ImportacaoArquivoVagas.objects.create(nome_arquivo='v.csv', arquivo='importacoes/v.csv', tipo='VAGAS')
    service = ApiEscolhasService(base_url='http://example.com')
    with patch('sigla_sdk.http.api_client.http_client.post', side_effect=RequestException('boom')):
        with pytest.raises(RequestException):
            service.enviar_vagas(registros=[{'A': '1'}], estrutura=[{'coluna': 'A', 'campo_payload': 'a'}], importacao_obj=obj)
    assert ImportacaoErro.objects.filter(object_id=obj.uuid).exists()

def test_transformar_registros_converte_data_sucesso() -> None:
    """Verifica transformar registros converte data sucesso.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = ApiEscolhasService()
    registros = [{'DATA': ' 05/09/2025 '}]
    estrutura = [{'coluna': 'DATA', 'campo_payload': 'data'}]
    out = service._transformar_registros(registros, estrutura)
    assert out == [{'data': '2025-09-05'}]

def test_transformar_registros_mantem_valor_quando_data_invalida() -> None:
    """Verifica transformar registros mantem valor quando data invalida.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = ApiEscolhasService()
    registros = [{'DATA': 'valor_invalido'}]
    estrutura = [{'coluna': 'DATA', 'campo_payload': 'data'}]
    out = service._transformar_registros(registros, estrutura)
    assert out == [{'data': 'valor_invalido'}]

def test_api_vagas_nao_quebra_quando_registrar_erro_falha() -> None:
    """Verifica api vagas nao quebra quando registrar erro falha.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    obj = ImportacaoArquivoVagas.objects.create(nome_arquivo='v2.csv', arquivo='importacoes/v2.csv', tipo='VAGAS')
    service = ApiEscolhasService(base_url='http://example.com')
    with patch('sigla_sdk.http.api_client.http_client.post', side_effect=RequestException('boom')):
        with pytest.raises(RequestException):
            service.enviar_vagas(registros=[{'A': '1'}], estrutura=[{'coluna': 'A', 'campo_payload': 'a'}], importacao_obj=obj)

class TestApiVagasConcursoFields:
    """Testes para os novos campos de concurso no ApiEscolhasService."""

    def test_enviar_vagas_com_campos_concurso(self) -> None:
        """Testa envio de vagas com campos de concurso preenchidos.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        import uuid
        service = ApiEscolhasService(base_url='https://api.exemplo')
        processo_uuid = str(uuid.uuid4())
        processo_nome = 'Processo Teste 2025'
        registros = [{'DataFechamentoModulo': '05/09/2025'}]
        estrutura = [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
        with patch('sigla_sdk.http.api_client.http_client.post') as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp
            service.enviar_vagas(registros=registros, estrutura=estrutura, processo_uuid=processo_uuid, processo_nome=processo_nome)
            args, kwargs = mock_post.call_args
            payload = kwargs['json']
            assert payload['processo_uuid'] == processo_uuid
            assert payload['processo_nome'] == processo_nome
            assert 'vagas' in payload

def test_enviar_vagas_erro_tipo_ue_desabilitado() -> None:
    """Verifica enviar vagas erro tipo ue desabilitado.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = ApiEscolhasService(base_url='https://api.exemplo')
    registros = [{'DataFechamentoModulo': '05/09/2025'}]
    estrutura = [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
    with patch('sigla_sdk.http.api_client.http_client.post') as mock_post:
        mock_resp = Mock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {'code': 'TIPO_UE_DESABILITADO', 'detail': 'Tipo de UE desabilitado'}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        with pytest.raises(TipoUEDesabilitadoException):
            service.enviar_vagas(registros=registros, estrutura=estrutura)

def test_enviar_vagas_erro_400_outro_codigo_gatilha_request_exception() -> None:
    """Verifica enviar vagas erro 400 outro codigo gatilha request exception.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = ApiEscolhasService(base_url='https://api.exemplo')
    registros = [{'DataFechamentoModulo': '05/09/2025'}]
    estrutura = [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
    with patch('sigla_sdk.http.api_client.http_client.post') as mock_post:
        mock_resp = Mock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {'code': 'OUTRO', 'detail': 'erro genérico'}
        mock_resp.text = '{"code":"OUTRO","detail":"erro genérico"}'
        mock_post.return_value = mock_resp
        with pytest.raises(ApiEscolhasException) as exc_info:
            service.enviar_vagas(registros=registros, estrutura=estrutura)
        exc = exc_info.value
        assert exc.status_code == 400
        assert exc.mensagem == 'Falha ao enviar vagas para API externa'
        assert 'erro genérico' in (exc.detalhes or '')

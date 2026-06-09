"""Módulo tests/views/test_importacao_habilitados."""
from __future__ import annotations
from typing import Any
import uuid
from unittest.mock import Mock, patch
import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from importa_arquivos.models import ImportacaoArquivoHabilitado, ImportacaoErro
from importa_arquivos.services.exceptions import ApiCandidatosException, ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException
pytestmark = pytest.mark.django_db

def test_importacao_habilitados_create_success(api_client: Any, settings: Any) -> None:
    """Verifica importacao habilitados create success.
    
    Args:
        api_client: Cliente de API para requisições de teste.
        settings: Parâmetro settings da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')
    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar, patch('importa_arquivos.views.importacao_habilitados.ApiCandidatosService') as mock_api:
        mock_validar.return_value = ([{'Inscricao': '123', 'Nome': 'Joao'}], [{'coluna': 'Inscricao', 'campo_payload': 'codigo_inscricao'}])
        mock_api.return_value.enviar_habilitados.return_value = Mock()
        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {'arquivo': arquivo, 'concurso_uuid': '11111111-1111-1111-1111-111111111111', 'concurso_nome': 'Concurso X', 'tipo': 'HABILITADOS'}, format='multipart')
        assert resp.status_code in (200, 201)
        assert resp.data['status'] == 'CONCLUIDO'
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_habilitados.assert_called_once()

def test_importacao_habilitados_cria_arquivo_com_validation_error(api_client: Any) -> None:
    """Verifica importacao habilitados cria arquivo com validation error.
    
    Args:
        api_client: Cliente de API para requisições de teste.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    arquivo = SimpleUploadedFile('h.csv', b'invalid', content_type='text/csv')
    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar:
        mock_validar.side_effect = ValueError('erro de layout')
        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {'arquivo': arquivo, 'concurso_uuid': '11111111-1111-1111-1111-111111111111', 'concurso_nome': 'Concurso X', 'tipo': 'HABILITADOS'}, format='multipart')
        assert resp.status_code == 400

@pytest.mark.parametrize('exception_cls,mensagem_esperada,detalhes_esperados', [(ColunaCSVInvalidaException, 'Coluna inválida no CSV', 'Coluna X não encontrada'), (LayoutNaoConfiguradoException, 'Layout não configurado', 'Layout para HABILITADOS inexistente'), (LeituraCSVException, 'Erro ao ler CSV', 'Arquivo corrompido')])
def test_importacao_habilitados_create_retorna_400_com_mensagem_e_detalhes(api_client: Any, exception_cls: Any, mensagem_esperada: Any, detalhes_esperados: Any) -> None:
    """Testa exceções de importação retornando 400 com detail e detalhes.
    
    Args:
        api_client: Cliente de API para requisições de teste.
        exception_cls: Parâmetro exception cls da operação.
        mensagem_esperada: Parâmetro mensagem esperada da operação.
        detalhes_esperados: Parâmetro detalhes esperados da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')
    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar:
        mock_validar.side_effect = exception_cls(mensagem=mensagem_esperada, detalhes=detalhes_esperados)
        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {'arquivo': arquivo, 'concurso_uuid': '11111111-1111-1111-1111-111111111111', 'concurso_nome': 'Concurso X', 'tipo': 'HABILITADOS'}, format='multipart')
        assert resp.status_code == 400
        assert resp.data['detail'] == mensagem_esperada
        assert resp.data['detalhes'] == detalhes_esperados

def test_importacao_habilitados_cria_arquivo_sem_arquivo(api_client: Any) -> None:
    """Verifica importacao habilitados cria arquivo sem arquivo.
    
    Args:
        api_client: Cliente de API para requisições de teste.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    url = reverse('importacao-arquivo-habilitados-list')
    resp = api_client.post(url, {'concurso_uuid': '11111111-1111-1111-1111-111111111111', 'concurso_nome': 'Concurso X', 'tipo': 'HABILITADOS'}, format='multipart')
    assert resp.status_code == 400

def test_importacao_habilitados_cria_arquivo_com_exception(api_client: Any) -> None:
    """Verifica importacao habilitados cria arquivo com exception.
    
    Args:
        api_client: Cliente de API para requisições de teste.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    arquivo = SimpleUploadedFile('h.csv', b'invalid', content_type='text/csv')
    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar:
        mock_validar.side_effect = Exception('boom')
        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {'arquivo': arquivo, 'concurso_uuid': '11111111-1111-1111-1111-111111111111', 'concurso_nome': 'Concurso X', 'tipo': 'HABILITADOS'}, format='multipart')
        assert resp.status_code == 400

def test_importacao_habilitados_envio_api_exception(api_client: Any, settings: Any) -> None:
    """Verifica importacao habilitados envio api exception.
    
    Args:
        api_client: Cliente de API para requisições de teste.
        settings: Parâmetro settings da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')
    with patch('importa_arquivos.views.importacao_habilitados.validar_csv_habilitados') as mock_validar, patch('importa_arquivos.views.importacao_habilitados.ApiCandidatosService') as mock_api:
        mock_validar.return_value = ([{'Inscricao': '123', 'Nome': 'Joao'}], [{'coluna': 'Inscricao', 'campo_payload': 'codigo_inscricao'}])
        mock_api.return_value.enviar_habilitados.side_effect = ApiCandidatosException(mensagem='Erro externo', detalhes='Detalhes do erro externo', status_code=400, code='ERRO_EXTERNO')
        url = reverse('importacao-arquivo-habilitados-list')
        resp = api_client.post(url, {'arquivo': arquivo, 'concurso_uuid': '11111111-1111-1111-1111-111111111111', 'concurso_nome': 'Concurso X', 'tipo': 'HABILITADOS'}, format='multipart')
        assert resp.status_code == 400
        assert resp.data['detail'] == 'Erro externo'
        assert resp.data['detalhes'] == 'Detalhes do erro externo'
        assert resp.data['status_code'] == 400
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_habilitados.assert_called_once()

def test_download_erros_retorna_arquivo_vazio_quando_sem_erros(api_client: Any) -> None:
    """Testa download_erros retorna arquivo vazio quando não há erros.
    
    Args:
        api_client: Cliente de API para requisições de teste.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    url = reverse('importacao-arquivo-habilitados-download-erros')
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/plain; charset=utf-8'
    assert 'attachment' in resp['Content-Disposition']
    assert 'habilitados_erros_' in resp['Content-Disposition']
    assert resp.content == b''

def test_download_erros_formata_conteudo_corretamente(api_client: Any) -> None:
    """Testa download_erros formata erros com titulo: conteudo.
    
    Args:
        api_client: Cliente de API para requisições de teste.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')
    importacao = ImportacaoArquivoHabilitado.objects.create(nome_arquivo='h.csv', arquivo=arquivo, tipo='HABILITADOS', concurso_uuid=uuid.uuid4(), concurso_nome='Concurso X')
    content_type = ContentType.objects.get_for_model(ImportacaoArquivoHabilitado)
    ImportacaoErro.objects.create(content_type=content_type, object_id=importacao.uuid, mensagem='Erro de teste', erros='Linha 1: erro na linha 1 | Linha 2: erro na linha 2')
    url = reverse('importacao-arquivo-habilitados-download-erros')
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/plain; charset=utf-8'
    assert 'attachment' in resp['Content-Disposition']
    conteudo = resp.content.decode('utf-8')
    assert '**Linha 1:** erro na linha 1' in conteudo
    assert '**Linha 2:** erro na linha 2' in conteudo

def test_download_erros_parte_sem_dois_pontos_apenas_append(api_client: Any) -> None:
    """Testa download_erros: partes sem ':' são adicionadas como estão.
    
    Args:
        api_client: Cliente de API para requisições de teste.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')
    importacao = ImportacaoArquivoHabilitado.objects.create(nome_arquivo='h.csv', arquivo=arquivo, tipo='HABILITADOS', concurso_uuid=uuid.uuid4(), concurso_nome='Concurso X')
    content_type = ContentType.objects.get_for_model(ImportacaoArquivoHabilitado)
    ImportacaoErro.objects.create(content_type=content_type, object_id=importacao.uuid, mensagem='Erro', erros='Mensagem simples sem dois pontos')
    url = reverse('importacao-arquivo-habilitados-download-erros')
    resp = api_client.get(url)
    assert resp.status_code == 200
    conteudo = resp.content.decode('utf-8')
    assert 'Mensagem simples sem dois pontos' in conteudo

def test_download_erros_filtra_por_importacao_uuid(api_client: Any) -> None:
    """Testa download_erros filtra por importacao_uuid quando informado.
    
    Args:
        api_client: Cliente de API para requisições de teste.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n123,Joao\n', content_type='text/csv')
    importacao1 = ImportacaoArquivoHabilitado.objects.create(nome_arquivo='h1.csv', arquivo=arquivo, tipo='HABILITADOS', concurso_uuid=uuid.uuid4(), concurso_nome='Concurso X')
    arquivo2 = SimpleUploadedFile('h2.csv', b'Inscricao,Nome\n456,Maria\n', content_type='text/csv')
    importacao2 = ImportacaoArquivoHabilitado.objects.create(nome_arquivo='h2.csv', arquivo=arquivo2, tipo='HABILITADOS', concurso_uuid=uuid.uuid4(), concurso_nome='Concurso Y')
    content_type = ContentType.objects.get_for_model(ImportacaoArquivoHabilitado)
    ImportacaoErro.objects.create(content_type=content_type, object_id=importacao1.uuid, mensagem='Erro 1', erros='Erro importacao 1')
    ImportacaoErro.objects.create(content_type=content_type, object_id=importacao2.uuid, mensagem='Erro 2', erros='Erro importacao 2')
    url = reverse('importacao-arquivo-habilitados-download-erros')
    resp = api_client.get(url, {'importacao_uuid': str(importacao1.uuid)})
    assert resp.status_code == 200
    conteudo = resp.content.decode('utf-8')
    assert 'Erro importacao 1' in conteudo
    assert 'Erro importacao 2' not in conteudo

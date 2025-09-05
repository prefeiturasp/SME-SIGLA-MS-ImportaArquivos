import pytest
from unittest.mock import patch, Mock
from django.urls import reverse
from rest_framework import status
from importa_arquivos.models import ImportacaoArquivos, Layout
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError


pytestmark = pytest.mark.django_db


 
def test_list_importacoes_arquivos_success(api_client, importacoes_arquivos):
    """Testa se a listagem de importações de arquivos retorna sucesso."""
    url = reverse('importacao-arquivo-list')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 3
    
    # Verificar se os dados estão corretos
    importacoes_data = response.data['results']
    importacao_nomes = [importacao['nome'] for importacao in importacoes_data]
    assert 'Arquivo de Teste' in importacao_nomes
    assert 'Arquivo Processando' in importacao_nomes
    assert 'Arquivo Concluído' in importacao_nomes
 
def test_list_importacoes_arquivos_empty(api_client):
    """Testa listagem quando não há importações."""
    url = reverse('importacao-arquivo-list')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 0

def test_create_importacao_arquivo_success(api_client):
    """Testa se a criação de importação de arquivo funciona corretamente."""
    arquivo = SimpleUploadedFile("novo_arquivo.csv", b"conteudo,novo", content_type="text/csv")
    data = {
        'nome': 'Novo Arquivo de Teste',
        'descricao': 'Descrição do novo arquivo',
        'arquivo': arquivo,
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_201_CREATED
    assert ImportacaoArquivos.objects.count() == 1
    
    # Verificar se a importação foi criada corretamente
    nova_importacao = ImportacaoArquivos.objects.get(nome='Novo Arquivo de Teste')
    assert nova_importacao.uuid is not None
    assert nova_importacao.criado_em is not None
    assert nova_importacao.atualizado_em is not None
    assert nova_importacao.status == 'pendente'
    assert nova_importacao.descricao == 'Descrição do novo arquivo'

def test_create_importacao_arquivo_without_nome(api_client):
    """Testa se a criação sem nome retorna erro."""
    arquivo = SimpleUploadedFile("arquivo.csv", b"conteudo", content_type="text/csv")
    data = {
        'arquivo': arquivo,
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'nome' in response.data

def test_create_importacao_arquivo_without_arquivo(api_client):
    """Testa se a criação sem arquivo retorna erro."""
    data = {
        'nome': 'Teste sem arquivo',
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'arquivo' in response.data

def test_create_importacao_arquivo_invalid_status(api_client):
    """Testa se a criação com status inválido retorna erro."""
    arquivo = SimpleUploadedFile("arquivo.csv", b"conteudo", content_type="text/csv")
    data = {
        'nome': 'Teste',
        'arquivo': arquivo,
        'status': 'status_invalido'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'status' in response.data

def test_retrieve_importacao_arquivo_success(api_client, importacao_arquivo_pendente):
    """Testa se a recuperação de importação de arquivo funciona corretamente."""
    url = reverse('importacao-arquivo-detail', kwargs={'pk': importacao_arquivo_pendente.uuid})
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['nome'] == 'Arquivo de Teste'
    assert response.data['status'] == 'pendente'
    assert response.data['uuid'] == str(importacao_arquivo_pendente.uuid)
    assert response.data['descricao'] == 'Descrição do arquivo de teste'

def test_retrieve_importacao_arquivo_not_found(api_client, fake_uuid):
    """Testa se retorna 404 para importação de arquivo inexistente."""
    url = reverse('importacao-arquivo-detail', kwargs={'pk': fake_uuid})
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_importacao_arquivo_success(api_client, importacao_arquivo_pendente):
    """Testa se a atualização de importação de arquivo funciona corretamente."""
    arquivo = SimpleUploadedFile("arquivo_atualizado.csv", b"conteudo,atualizado", content_type="text/csv")
    data = {
        'nome': 'Arquivo Atualizado',
        'descricao': 'Descrição atualizada',
        'arquivo': arquivo,
        'status': 'processando'
    }
    
    url = reverse('importacao-arquivo-detail', kwargs={'pk': importacao_arquivo_pendente.uuid})
    response = api_client.put(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['nome'] == 'Arquivo Atualizado'
    assert response.data['status'] == 'processando'
    assert response.data['descricao'] == 'Descrição atualizada'
    
    # Verificar se foi atualizado no banco
    importacao_arquivo_pendente.refresh_from_db()
    assert importacao_arquivo_pendente.nome == 'Arquivo Atualizado'
    assert importacao_arquivo_pendente.status == 'processando'
    assert importacao_arquivo_pendente.descricao == 'Descrição atualizada'

def test_partial_update_importacao_arquivo_success(api_client, importacao_arquivo_pendente):
    """Testa se a atualização parcial funciona corretamente."""
    data = {
        'status': 'processando',
        'descricao': 'Nova descrição'
    }
    
    url = reverse('importacao-arquivo-detail', kwargs={'pk': importacao_arquivo_pendente.uuid})
    response = api_client.patch(url, data)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['status'] == 'processando'
    assert response.data['descricao'] == 'Nova descrição'
    # Nome deve permanecer o mesmo
    assert response.data['nome'] == 'Arquivo de Teste'
    
    # Verificar se foi atualizado no banco
    importacao_arquivo_pendente.refresh_from_db()
    assert importacao_arquivo_pendente.status == 'processando'
    assert importacao_arquivo_pendente.descricao == 'Nova descrição'
    assert importacao_arquivo_pendente.nome == 'Arquivo de Teste'

def test_delete_importacao_arquivo_success(api_client, importacao_arquivo_pendente):
    """Testa se a exclusão de importação de arquivo funciona corretamente."""
    url = reverse('importacao-arquivo-detail', kwargs={'pk': importacao_arquivo_pendente.uuid})
    response = api_client.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ImportacaoArquivos.objects.count() == 0
    
    # Verificar se a importação foi realmente excluída
    with pytest.raises(ImportacaoArquivos.DoesNotExist):
        ImportacaoArquivos.objects.get(uuid=importacao_arquivo_pendente.uuid)

# =====================================
# NOVOS TESTES PARA STATUS CODES E VALIDAÇÃO
# =====================================

def test_create_importacao_validation_error_returns_422(api_client, layout_vagas):
    """Testa se erro de validação retorna status 422."""
    # Arquivo com headers incorretos para layout VAGAS
    csv_content = b"Campo1,Campo2,Campo3\nvalor1,valor2,valor3"
    arquivo = SimpleUploadedFile("teste_erro.csv", csv_content, content_type="text/csv")
    
    data = {
        'nome': 'Teste Validação Erro',
        'descricao': 'Teste que deve falhar na validação',
        'arquivo': arquivo,
        'tipo_de_layout': 'VAGAS',
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert 'validation_errors' in response.data
    assert ImportacaoArquivos.objects.count() == 0

def test_create_importacao_bad_request_returns_400(api_client):
    """Testa se dados inválidos retornam status 400."""
    data = {
        'nome': '',  # Nome vazio deve gerar erro 400
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert ImportacaoArquivos.objects.count() == 0

def test_retrieve_not_found_returns_404(api_client):
    """Testa se recurso não encontrado retorna status 404."""
    fake_uuid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    url = reverse('importacao-arquivo-detail', kwargs={'pk': fake_uuid})
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'detail' in response.data

def test_update_not_found_returns_404(api_client):
    """Testa se atualização de recurso inexistente retorna 404."""
    fake_uuid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    data = {'nome': 'Teste'}
    
    url = reverse('importacao-arquivo-detail', kwargs={'pk': fake_uuid})
    response = api_client.patch(url, data)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_not_found_returns_404(api_client):
    """Testa se exclusão de recurso inexistente retorna 404."""
    fake_uuid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    
    url = reverse('importacao-arquivo-detail', kwargs={'pk': fake_uuid})
    response = api_client.delete(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@patch('importa_arquivos.services.requests.post')
def test_create_importacao_robust_server_success(mock_post, api_client, layout_vagas):
    """Testa se a integração com robust_server funciona corretamente."""
    # Mock da resposta do robust_server
    mock_response = Mock()
    mock_response.status_code = status.HTTP_201_CREATED
    mock_post.return_value = mock_response
    
    # Arquivo com headers corretos para layout VAGAS
    csv_content = b"Inscricao,Nome,DataNascimento\n12345,Teste,1990-01-01"
    arquivo = SimpleUploadedFile("vagas_teste.csv", csv_content, content_type="text/csv")
    
    data = {
        'nome': 'Teste Integração Robust Server',
        'descricao': 'Teste da integração',
        'arquivo': arquivo,
        'tipo_de_layout': 'VAGAS',
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar se o arquivo foi criado no banco
    importacao = ImportacaoArquivos.objects.get(nome='Teste Integração Robust Server')
    assert importacao.status == 'processando'  # Status deve ter sido atualizado
    assert importacao.arquivo_nome_original == 'vagas_teste.csv'
    assert importacao.arquivo_tamanho > 0
    
    # Verificar se o requests.post foi chamado
    assert mock_post.called

@patch('importa_arquivos.services.requests.post')
def test_create_importacao_robust_server_error(mock_post, api_client, layout_vagas):
    """Testa se erro no robust_server atualiza status para erro."""
    # Mock da resposta de erro do robust_server
    mock_response = Mock()
    mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_post.return_value = mock_response
    
    # Arquivo com headers corretos para layout VAGAS
    csv_content = b"Inscricao,Nome,DataNascimento\n12345,Teste,1990-01-01"
    arquivo = SimpleUploadedFile("vagas_erro.csv", csv_content, content_type="text/csv")
    
    data = {
        'nome': 'Teste Erro Robust Server',
        'arquivo': arquivo,
        'tipo_de_layout': 'VAGAS',
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar se o status foi atualizado para erro
    importacao = ImportacaoArquivos.objects.get(nome='Teste Erro Robust Server')
    assert importacao.status == 'erro'

@patch('importa_arquivos.services.requests.post')
def test_create_importacao_robust_server_connection_error(mock_post, api_client, layout_vagas):
    """Testa se erro de conexão com robust_server atualiza status para erro."""
    # Mock de erro de conexão
    from requests.exceptions import ConnectionError
    mock_post.side_effect = ConnectionError("Connection refused")
    
    # Arquivo com headers corretos para layout VAGAS
    csv_content = b"Inscricao,Nome,DataNascimento\n12345,Teste,1990-01-01"
    arquivo = SimpleUploadedFile("vagas_conexao_erro.csv", csv_content, content_type="text/csv")
    
    data = {
        'nome': 'Teste Erro Conexão',
        'arquivo': arquivo,
        'tipo_de_layout': 'VAGAS',
        'status': 'pendente'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar se o status foi atualizado para erro devido ao erro de conexão
    importacao = ImportacaoArquivos.objects.get(nome='Teste Erro Conexão')
    assert importacao.status == 'erro'

def test_create_importacao_arquivo_metadata_fields(api_client, layout_vagas):
    """Testa se os campos de metadata são preenchidos corretamente."""
    csv_content = b"Inscricao,Nome,DataNascimento\n12345,Teste,1990-01-01"
    arquivo = SimpleUploadedFile("metadata_test.csv", csv_content, content_type="text/csv")
    
    data = {
        'nome': 'Teste Metadata',
        'arquivo': arquivo,
        'tipo_de_layout': 'VAGAS'
    }
    
    url = reverse('importacao-arquivo-list')
    response = api_client.post(url, data, format='multipart')
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar campos de metadata na resposta
    assert 'arquivo_nome_original' in response.data
    assert 'arquivo_tamanho' in response.data
    assert 'arquivo_content_type' in response.data
    assert response.data['arquivo_nome_original'] == 'metadata_test.csv'
    assert response.data['arquivo_tamanho'] > 0
    assert response.data['arquivo_content_type'] == 'text/csv'

def test_layouts_endpoint_status_codes(api_client):
    """Testa se endpoints de layout retornam status codes corretos."""
    # Testar GET /layouts/
    url = reverse('layout-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    
    # Testar GET /layouts/tipos_disponiveis/
    url = reverse('layout-tipos-disponiveis')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)

def test_error_handling_in_views(api_client):
    """Testa tratamento de erros nos views."""
    # Simular erro interno tentando criar importação com dados problemáticos
    with patch('importa_arquivos.serializers.ImportacaoArquivosSerializer.create') as mock_create:
        mock_create.side_effect = Exception("Erro interno simulado")
        
        arquivo = SimpleUploadedFile("erro_interno.csv", b"test", content_type="text/csv")
        data = {
            'nome': 'Teste Erro Interno',
            'arquivo': arquivo
        }
        
        url = reverse('importacao-arquivo-list')
        response = api_client.post(url, data, format='multipart')
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data


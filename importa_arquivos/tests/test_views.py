import pytest
from django.urls import reverse
from rest_framework import status
from importa_arquivos.models import ImportacaoArquivos
from django.core.files.uploadedfile import SimpleUploadedFile


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


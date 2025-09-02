import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from importa_arquivos.models import ImportacaoArquivos
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def api_client():
    """
    Fixture para criar um cliente API de teste.
    """
    return APIClient()

 

 

@pytest.fixture
def importacao_arquivo_pendente():
    """
    Fixture para criar uma importação de arquivo pendente.
    """
    arquivo = SimpleUploadedFile("teste.csv", b"conteudo,do,arquivo", content_type="text/csv")
    return ImportacaoArquivos.objects.create(
        nome='Arquivo de Teste',
        descricao='Descrição do arquivo de teste',
        arquivo=arquivo,
        status='pendente'
    )


@pytest.fixture
def importacao_arquivo_processando():
    """
    Fixture para criar uma importação de arquivo em processamento.
    """
    arquivo = SimpleUploadedFile("processando.csv", b"conteudo,processando", content_type="text/csv")
    return ImportacaoArquivos.objects.create(
        nome='Arquivo Processando',
        descricao='Arquivo em processamento',
        arquivo=arquivo,
        status='processando'
    )


@pytest.fixture
def importacao_arquivo_concluido():
    """
    Fixture para criar uma importação de arquivo concluída.
    """
    arquivo = SimpleUploadedFile("concluido.csv", b"conteudo,concluido", content_type="text/csv")
    return ImportacaoArquivos.objects.create(
        nome='Arquivo Concluído',
        descricao='Arquivo processado com sucesso',
        arquivo=arquivo,
        status='concluido'
    )


@pytest.fixture
def importacoes_arquivos(importacao_arquivo_pendente, importacao_arquivo_processando, importacao_arquivo_concluido):
    """
    Fixture para criar múltiplas importações de arquivos de teste.
    """
    return [importacao_arquivo_pendente, importacao_arquivo_processando, importacao_arquivo_concluido]


@pytest.fixture
def importacao_arquivo_data():
    """
    Fixture para dados de importação de arquivo válidos.
    """
    arquivo = SimpleUploadedFile("novo_arquivo.csv", b"conteudo,novo", content_type="text/csv")
    return {
        'nome': 'Novo Arquivo de Teste',
        'descricao': 'Descrição do novo arquivo',
        'arquivo': arquivo,
        'status': 'pendente'
    }


@pytest.fixture
def fake_uuid():
    """
    Fixture para gerar UUIDs falsos para testes.
    """
    return uuid.uuid4()


@pytest.fixture
def multiple_importacoes_arquivos():
    """
    Fixture para criar múltiplas importações de arquivos para testes de paginação.
    """
    importacoes = []
    for i in range(25):
        arquivo = SimpleUploadedFile(f"arquivo_{i}.csv", f"conteudo,{i}".encode(), content_type="text/csv")
        importacao = ImportacaoArquivos.objects.create(
            nome=f'Importação Teste {i}',
            descricao=f'Descrição {i}',
            arquivo=arquivo,
            status='pendente'
        )
        importacoes.append(importacao)
    return importacoes

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from importa_arquivos.models import ImportacaoArquivos, Layout
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def api_client():
    """
    Fixture para criar um cliente API de teste.
    """
    return APIClient()

 

 

@pytest.fixture
def layout_vagas():
    """
    Fixture para criar um layout VAGAS.
    """
    return Layout.objects.create(
        tipo_de_layout='VAGAS',
        dados=[
            {"ordem": 1, "campo": "Inscricao", "tipo": "string", "tamanho": 20, "regras_de_validacao": "obrigatorio,unico"},
            {"ordem": 2, "campo": "Nome", "tipo": "string", "tamanho": 200, "regras_de_validacao": "obrigatorio"},
            {"ordem": 3, "campo": "DataNascimento", "tipo": "date", "tamanho": 10, "regras_de_validacao": "obrigatorio,data_valida"}
        ]
    )

@pytest.fixture
def importacao_arquivo_pendente():
    """
    Fixture para criar uma importação de arquivo pendente.
    """
    arquivo = SimpleUploadedFile("teste.csv", b"conteudo,do,arquivo", content_type="text/csv")
    importacao = ImportacaoArquivos(
        nome='Arquivo de Teste',
        descricao='Descrição do arquivo de teste',
        status='pendente'
    )
    importacao.set_arquivo_temporario(arquivo)
    importacao.save()
    return importacao


@pytest.fixture
def importacao_arquivo_processando():
    """
    Fixture para criar uma importação de arquivo em processamento.
    """
    arquivo = SimpleUploadedFile("processando.csv", b"conteudo,processando", content_type="text/csv")
    importacao = ImportacaoArquivos(
        nome='Arquivo Processando',
        descricao='Arquivo em processamento',
        status='processando'
    )
    importacao.set_arquivo_temporario(arquivo)
    importacao.save()
    return importacao


@pytest.fixture
def importacao_arquivo_concluido():
    """
    Fixture para criar uma importação de arquivo concluída.
    """
    arquivo = SimpleUploadedFile("concluido.csv", b"conteudo,concluido", content_type="text/csv")
    importacao = ImportacaoArquivos(
        nome='Arquivo Concluído',
        descricao='Arquivo processado com sucesso',
        status='concluido'
    )
    importacao.set_arquivo_temporario(arquivo)
    importacao.save()
    return importacao


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

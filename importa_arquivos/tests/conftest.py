import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from importa_arquivos.models import ImportacaoArquivos
from importa_arquivos.layout_service import LayoutService
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
    Fixture para garantir que existe um layout VAGAS.
    """
    layout_data = {
        'uuid': '54eb3e0d-65ba-4e23-b7ee-580164ee0dc2',
        'tipo_de_layout': 'VAGAS',
        'dados': [
            {"ordem": 1, "campo": "Inscricao", "tipo": "string", "tamanho": 20, "regras_de_validacao": "obrigatorio,unico"},
            {"ordem": 2, "campo": "Nome", "tipo": "string", "tamanho": 200, "regras_de_validacao": "obrigatorio"},
            {"ordem": 3, "campo": "DataNascimento", "tipo": "date", "tamanho": 10, "regras_de_validacao": "obrigatorio,data_valida"}
        ],
        'total_campos': 3,
        'criado_em': '2025-09-04T11:07:13.371479-03:00'
    }
    
    # Verificar se já existe, se não, criar
    existing = LayoutService.get_layout_by_tipo('VAGAS')
    if not existing:
        LayoutService.create_layout(layout_data)
    
    return LayoutService.get_layout_by_tipo('VAGAS')

@pytest.fixture
def importacao_arquivo_pendente(layout_vagas):
    """
    Fixture para criar uma importação de arquivo pendente.
    """
    # Arquivo que corresponde ao layout VAGAS
    arquivo = SimpleUploadedFile("teste.csv", b"Inscricao,Nome,DataNascimento\n12345,Teste,1990-01-01", content_type="text/csv")
    importacao = ImportacaoArquivos(
        concurso='Concurso Teste',
        cargo='Cargo Teste',
        status='pendente',
        tipo_de_layout='VAGAS'
    )
    importacao.set_arquivo_temporario(arquivo)
    importacao.save()
    return importacao


@pytest.fixture
def importacao_arquivo_processando(layout_vagas):
    """
    Fixture para criar uma importação de arquivo em processamento.
    """
    arquivo = SimpleUploadedFile("processando.csv", b"Inscricao,Nome,DataNascimento\n67890,Processando,1985-05-15", content_type="text/csv")
    importacao = ImportacaoArquivos(
        concurso='Concurso Processando',
        cargo='Cargo Processando',
        status='processando',
        tipo_de_layout='VAGAS'
    )
    importacao.set_arquivo_temporario(arquivo)
    importacao.save()
    return importacao


@pytest.fixture
def importacao_arquivo_concluido(layout_vagas):
    """
    Fixture para criar uma importação de arquivo concluída.
    """
    arquivo = SimpleUploadedFile("concluido.csv", b"Inscricao,Nome,DataNascimento\n11111,Concluido,1990-12-25", content_type="text/csv")
    importacao = ImportacaoArquivos(
        concurso='Concurso Concluído',
        cargo='Cargo Concluído',
        status='concluido',
        tipo_de_layout='VAGAS'
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
        'concurso': 'Novo Concurso de Teste',
        'cargo': 'Novo Cargo de Teste',
        'arquivo': arquivo
    }


@pytest.fixture
def fake_uuid():
    """
    Fixture para gerar UUIDs falsos para testes.
    """
    return uuid.uuid4()


@pytest.fixture
def importacao_sem_validacao():
    """
    Fixture para criar importação sem validação de arquivo.
    """
    return ImportacaoArquivos.objects.create(
        concurso='Concurso Sem Validação',
        cargo='Cargo Sem Validação',
        status='pendente',
        tipo_de_layout='VAGAS'
    )

@pytest.fixture
def multiple_importacoes_arquivos(layout_vagas):
    """
    Fixture para criar múltiplas importações de arquivos para testes de paginação.
    """
    importacoes = []
    for i in range(25):
        importacao = ImportacaoArquivos.objects.create(
            concurso=f'Concurso Teste {i}',
            cargo=f'Cargo Teste {i}',
            status='pendente',
            tipo_de_layout='VAGAS'
        )
        importacoes.append(importacao)
    return importacoes

import uuid
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch, Mock

from importa_arquivos.models import ImportacaoArquivoVagas, ImportacaoErro
from importa_arquivos.services.exceptions import TipoUEDesabilitadoException, ApiEscolhasException

pytestmark = pytest.mark.django_db


def test_importacao_vagas_create_success(api_client, settings):
    settings.ESCOLHAS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
         patch('importa_arquivos.views.importacao_vagas.ApiEscolhasService') as mock_api:
        mock_validar.return_value = (
            [{'DataFechamentoModulo': '05/09/2025'}],
            [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
        )
        mock_api.return_value.enviar_vagas.return_value = Mock()

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code in (200, 201)
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_vagas.assert_called_once()


def test_importacao_vagas_create_validation_error(api_client):
    arquivo = SimpleUploadedFile('v.csv', b'invalid', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar:
        mock_validar.side_effect = ValueError('erro de layout') 

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code == 400


def test_importacao_vagas_create_unexpected_exception(api_client):
    arquivo = SimpleUploadedFile('v.csv', b'invalid', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar:
        mock_validar.side_effect = Exception('boom')

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code == 400
        assert resp.data.get('detail') == 'Erro ao validar CSV.'


def test_importacao_vagas_envio_api_exception(api_client, settings):
    settings.ESCOLHAS_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
         patch('importa_arquivos.views.importacao_vagas.ApiEscolhasService') as mock_api:
        mock_validar.return_value = (
            [{'DataFechamentoModulo': '05/09/2025'}],
            [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
        )
        mock_api.return_value.enviar_vagas.side_effect = ApiEscolhasException(
            mensagem='Erro externo',
            detalhes='Detalhes do erro externo',
            status_code=400,
            code='ERRO_EXTERNO',
        )

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code == 400
        assert resp.data['detail'] == 'Erro externo'
        assert resp.data['detalhes'] == 'Detalhes do erro externo'
        assert resp.data['status_code'] == 400
        mock_validar.assert_called_once()
        mock_api.return_value.enviar_vagas.assert_called_once()


def test_importacao_vagas_tipo_ue_desabilitado(api_client, settings):
    settings.ESCOLHA_API_URL = 'https://api.exemplo'
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

    with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
         patch('importa_arquivos.views.importacao_vagas.ApiEscolhasService') as mock_api:
        mock_validar.return_value = (
            [{'DataFechamentoModulo': '05/09/2025', 'codigo_eol': '123456'}],
            [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
        )
        mock_api.return_value.enviar_vagas.side_effect = TipoUEDesabilitadoException('Tipo de UE desabilitado', 'TIPO_UE_DESABILITADO')

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.post(url, {
            'arquivo': arquivo,
            'tipo': 'VAGAS',
        }, format='multipart')

        assert resp.status_code == 400
        assert resp.data.get('code') == 'TIPO_UE_DESABILITADO'
        assert 'Tipo de UE desabilitado' in resp.data.get('detail', '')


def test_importacao_vagas_list_success(api_client, cria_vagas):
    cria_vagas([
        ('teste1.csv', 'PENDENTE'),
        ('teste2.csv', 'PROCESSADO'),
    ])

    url = reverse('importacao-arquivo-vagas-list')
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert 'results' in resp.data
    assert len(resp.data['results']) == 2
    assert resp.data['results'][0]['nome_arquivo'] in ['teste1.csv', 'teste2.csv']


def test_importacao_vagas_retrieve_success(api_client, cria_vagas):
    objs = cria_vagas([
        ('teste.csv', 'PENDENTE'),
    ])
    obj = objs[0]

    url = reverse('importacao-arquivo-vagas-detail', kwargs={'pk': obj.pk})
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert resp.data['nome_arquivo'] == 'teste.csv'
    assert resp.data['status'] == 'PENDENTE'
    assert 'uuid' in resp.data


# Testes para as novas funcionalidades de filtros e busca
class TestImportacaoVagasFiltersAndSearch:
    """Testes para funcionalidades de filtros e busca adicionadas."""

    def test_filterset_fields_nome_arquivo(self, api_client, cria_vagas):
        """Testa filtro por nome_arquivo."""
        cria_vagas([
            ('arquivo1.csv', 'PENDENTE'),
            ('arquivo2.csv', 'PROCESSADO'),
        ])

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.get(url, {'nome_arquivo': 'arquivo1.csv'})

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['nome_arquivo'] == 'arquivo1.csv'

    def test_filterset_fields_status(self, api_client, cria_vagas):
        """Testa filtro por status."""
        cria_vagas([
            ('arquivo1.csv', 'PENDENTE'),
            ('arquivo2.csv', 'PROCESSADO'),
        ])

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.get(url, {'status': 'PENDENTE'})

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['status'] == 'PENDENTE'

    def test_filterset_fields_processo_uuid(self, api_client):
        """Testa filtro por processo_uuid."""
        import uuid
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.models import ImportacaoArquivoVagas
        
        processo_uuid = str(uuid.uuid4())
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo1.csv',
            arquivo=SimpleUploadedFile('arquivo1.csv', b'content'),
            status='PENDENTE',
            processo_uuid=processo_uuid,
            processo_nome='Processo Teste 1'
        )
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo2.csv',
            arquivo=SimpleUploadedFile('arquivo2.csv', b'content'),
            status='PROCESSADO',
            processo_uuid=str(uuid.uuid4()),
            processo_nome='Processo Teste 2'
        )

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.get(url, {'processo_uuid': processo_uuid})

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['processo_uuid'] == processo_uuid

    def test_filterset_fields_processo_nome(self, api_client):
        """Testa filtro por processo_nome."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.models import ImportacaoArquivoVagas
        
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo1.csv',
            arquivo=SimpleUploadedFile('arquivo1.csv', b'content'),
            status='PENDENTE',
            processo_nome='Processo Teste 1'
        )
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo2.csv',
            arquivo=SimpleUploadedFile('arquivo2.csv', b'content'),
            status='PROCESSADO',
            processo_nome='Processo Teste 2'
        )

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.get(url, {'processo_nome': 'Processo Teste 1'})

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['processo_nome'] == 'Processo Teste 1'

    def test_search_fields_processo_uuid(self, api_client):
        """Testa busca por processo_uuid."""
        import uuid
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.models import ImportacaoArquivoVagas
        
        processo_uuid = str(uuid.uuid4())
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo1.csv',
            arquivo=SimpleUploadedFile('arquivo1.csv', b'content'),
            status='PENDENTE',
            processo_uuid=processo_uuid,
            processo_nome='Processo Teste 1'
        )
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo2.csv',
            arquivo=SimpleUploadedFile('arquivo2.csv', b'content'),
            status='PROCESSADO',
            processo_uuid=str(uuid.uuid4()),
            processo_nome='Processo Teste 2'
        )

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.get(url, {'search': processo_uuid})

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['processo_uuid'] == processo_uuid

    def test_search_fields_processo_nome(self, api_client):
        """Testa busca por processo_nome."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.models import ImportacaoArquivoVagas
        
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo1.csv',
            arquivo=SimpleUploadedFile('arquivo1.csv', b'content'),
            status='PENDENTE',
            processo_nome='Processo Teste 1'
        )
        ImportacaoArquivoVagas.objects.create(
            nome_arquivo='arquivo2.csv',
            arquivo=SimpleUploadedFile('arquivo2.csv', b'content'),
            status='PROCESSADO',
            processo_nome='Processo Teste 2'
        )

        url = reverse('importacao-arquivo-vagas-list')
        resp = api_client.get(url, {'search': 'Processo Teste 1'})

        assert resp.status_code == 200
        assert len(resp.data['results']) == 1
        assert resp.data['results'][0]['processo_nome'] == 'Processo Teste 1'


# Testes para o tratamento dos campos de concurso no create
class TestImportacaoVagasConcursoFields:
    """Testes para o tratamento dos campos de processo no create."""

    def test_create_with_concurso_fields_in_serializer(self, api_client, settings):
        """Testa criação com campos de concurso no serializer."""
        settings.ESCOLHA_API_URL = 'https://api.exemplo'
        import uuid
        processo_uuid = str(uuid.uuid4())
        arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

        with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
            patch('importa_arquivos.views.importacao_vagas.ApiEscolhasService') as mock_api:
                mock_validar.return_value = (
                    [{'DataFechamentoModulo': '05/09/2025'}],
                    [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
                )
                mock_api.return_value.enviar_vagas.return_value = Mock()

                url = reverse('importacao-arquivo-vagas-list')
                resp = api_client.post(url, {
                    'arquivo': arquivo,
                    'processo_uuid': processo_uuid,
                    'processo_nome': 'Processo Teste',
                }, format='multipart')

                assert resp.status_code in (200, 201)
                mock_api.return_value.enviar_vagas.assert_called_once()
                # Verifica se os campos de concurso foram passados para a API
                call_args = mock_api.return_value.enviar_vagas.call_args
                assert call_args[1]['processo_uuid'] == processo_uuid
                assert call_args[1]['processo_nome'] == 'Processo Teste'

    def test_create_with_concurso_fields_in_request_data(self, api_client, settings):
        """Testa criação com campos de concurso no request.data."""
        settings.ESCOLHA_API_URL = 'https://api.exemplo'
        import uuid
        processo_uuid = str(uuid.uuid4())
        arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

        with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
             patch('importa_arquivos.views.importacao_vagas.ApiEscolhasService') as mock_api:
            mock_validar.return_value = (
                [{'DataFechamentoModulo': '05/09/2025'}],
                [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
            )
            mock_api.return_value.enviar_vagas.return_value = Mock()

            url = reverse('importacao-arquivo-vagas-list')
            resp = api_client.post(url, {
                'arquivo': arquivo,
                'processo_uuid': processo_uuid,
                'processo_nome': 'Processo Teste',
            }, format='multipart')

            assert resp.status_code in (200, 201)
            mock_api.return_value.enviar_vagas.assert_called_once()
            # Verifica se os campos de concurso foram passados para a API
            call_args = mock_api.return_value.enviar_vagas.call_args
            assert call_args[1]['processo_uuid'] == processo_uuid
            assert call_args[1]['processo_nome'] == 'Processo Teste'

    def test_create_with_empty_concurso_fields(self, api_client, settings):
        """Testa criação com campos de concurso vazios."""
        settings.ESCOLHA_API_URL = 'https://api.exemplo'
        arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

        with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
             patch('importa_arquivos.views.importacao_vagas.ApiEscolhasService') as mock_api:
            mock_validar.return_value = (
                [{'DataFechamentoModulo': '05/09/2025'}],
                [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
            )
            mock_api.return_value.enviar_vagas.return_value = Mock()

            url = reverse('importacao-arquivo-vagas-list')
            resp = api_client.post(url, {
                'arquivo': arquivo,
            }, format='multipart')

            assert resp.status_code in (200, 201)
            mock_api.return_value.enviar_vagas.assert_called_once()
            # Verifica se os campos de concurso vazios foram passados como string vazia
            call_args = mock_api.return_value.enviar_vagas.call_args
            assert call_args[1]['processo_uuid'] == ''
            assert call_args[1]['processo_nome'] == ''


# Testes para tratamento de erros com logging
class TestImportacaoVagasErrorHandling:
    """Testes para o tratamento de erros com logging."""

    def test_validation_error_with_logging(self, api_client):
        """Testa erro de validação com logging."""
        arquivo = SimpleUploadedFile('v.csv', b'invalid', content_type='text/csv')

        with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
             patch('importa_arquivos.views.importacao_vagas.logging') as mock_logging:
            mock_validar.side_effect = Exception('erro inesperado')

            url = reverse('importacao-arquivo-vagas-list')
            resp = api_client.post(url, {
                'arquivo': arquivo,
            }, format='multipart')

            assert resp.status_code == 400
            assert resp.data.get('detail') == 'Erro ao validar CSV.'
            # Verifica se o erro foi logado
            mock_logging.error.assert_called_once()
            assert 'Erro inesperado na validação do CSV' in mock_logging.error.call_args[0][0]

    def test_api_service_error_with_logging(self, api_client, settings):
        """Testa erro na API externa com logging."""
        settings.ESCOLHA_API_URL = 'https://api.exemplo'
        arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')

        with patch('importa_arquivos.views.importacao_vagas.validar_csv_vagas') as mock_validar, \
             patch('importa_arquivos.views.importacao_vagas.ApiEscolhasService') as mock_api, \
             patch('importa_arquivos.views.importacao_vagas.logging') as mock_logging:
            mock_validar.return_value = (
                [{'DataFechamentoModulo': '05/09/2025'}],
                [{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}]
            )
            mock_api.return_value.enviar_vagas.side_effect = ApiEscolhasException(
                mensagem='Erro externo',
                detalhes='Detalhes do erro externo',
                status_code=400,
                code='ERRO_EXTERNO',
            )

            url = reverse('importacao-arquivo-vagas-list')
            resp = api_client.post(url, {
                'arquivo': arquivo,
            }, format='multipart')

            assert resp.status_code == 400
            assert resp.data['detail'] == 'Erro externo'
            assert resp.data['detalhes'] == 'Detalhes do erro externo'
            assert resp.data['status_code'] == 400


# Testes para os serializers com campos de concurso
class TestImportacaoVagasSerializers:
    """Testes para os serializers com os novos campos de processo."""

    def test_create_serializer_with_concurso_fields(self):
        """Testa ImportacaoArquivoVagasCreateSerializer com campos de concurso."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.serializers import ImportacaoArquivoVagasCreateSerializer
        import uuid
        
        processo_uuid = str(uuid.uuid4())
        arquivo = SimpleUploadedFile('teste.csv', b'content')
        
        data = {
            'arquivo': arquivo,
            'processo_uuid': processo_uuid,
            'processo_nome': 'Processo Teste 2025'
        }
        
        serializer = ImportacaoArquivoVagasCreateSerializer(data=data)
        assert serializer.is_valid()
        
        instance = serializer.save()
        assert str(instance.processo_uuid) == processo_uuid
        assert instance.processo_nome == 'Processo Teste 2025'
        assert instance.nome_arquivo == 'teste.csv'
        assert instance.tipo == 'VAGAS'

    def test_create_serializer_without_concurso_fields(self):
        """Testa ImportacaoArquivoVagasCreateSerializer sem campos de concurso."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.serializers import ImportacaoArquivoVagasCreateSerializer
        
        arquivo = SimpleUploadedFile('teste.csv', b'content')
        
        data = {
            'arquivo': arquivo,
        }
        
        serializer = ImportacaoArquivoVagasCreateSerializer(data=data)
        assert serializer.is_valid()
        
        instance = serializer.save()
        assert instance.processo_uuid is None
        assert instance.processo_nome is None
        assert instance.nome_arquivo == 'teste.csv'
        assert instance.tipo == 'VAGAS'

    def test_list_serializer_includes_processo_fields(self, api_client):
        """Testa ImportacaoArquivoVagasListSerializer inclui campos de processo."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.models import ImportacaoArquivoVagas
        import uuid
        
        processo_uuid = str(uuid.uuid4())
        obj = ImportacaoArquivoVagas.objects.create(
            nome_arquivo='teste.csv',
            arquivo=SimpleUploadedFile('teste.csv', b'content'),
            status='PENDENTE',
            processo_uuid=processo_uuid,
            processo_nome='Processo Teste 2025'
        )
        
        url = reverse('importacao-arquivo-vagas-detail', kwargs={'pk': obj.pk})
        resp = api_client.get(url)
        
        assert resp.status_code == 200
        assert resp.data['processo_uuid'] == processo_uuid
        assert resp.data['processo_nome'] == 'Processo Teste 2025'
        assert 'uuid' in resp.data
        assert 'nome_arquivo' in resp.data
        assert 'status' in resp.data
        assert 'criado_em' in resp.data
        assert 'atualizado_em' in resp.data

    def test_list_serializer_with_null_processo_fields(self, api_client):
        """Testa ImportacaoArquivoVagasListSerializer com campos de processo nulos."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from importa_arquivos.models import ImportacaoArquivoVagas
        
        obj = ImportacaoArquivoVagas.objects.create(
            nome_arquivo='teste.csv',
            arquivo=SimpleUploadedFile('teste.csv', b'content'),
            status='PENDENTE',
            processo_uuid=None,
            processo_nome=None
        )
        
        url = reverse('importacao-arquivo-vagas-detail', kwargs={'pk': obj.pk})
        resp = api_client.get(url)
        
        assert resp.status_code == 200
        assert resp.data['processo_uuid'] is None
        assert resp.data['processo_nome'] is None
        assert 'uuid' in resp.data
        assert 'nome_arquivo' in resp.data
        assert 'status' in resp.data


# Testes para download_erros
def test_download_erros_retorna_arquivo_vazio_quando_sem_erros(api_client):
    """Testa download_erros retorna arquivo vazio quando não há erros."""
    url = reverse('importacao-arquivo-vagas-download-erros')
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/plain; charset=utf-8'
    assert 'attachment' in resp['Content-Disposition']
    assert 'vagas_erros_' in resp['Content-Disposition']
    assert resp.content == b''


def test_download_erros_formata_conteudo_corretamente(api_client):
    """Testa download_erros formata erros com titulo: conteudo."""
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')
    importacao = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='v.csv',
        arquivo=arquivo,
        tipo='VAGAS',
    )
    content_type = ContentType.objects.get_for_model(ImportacaoArquivoVagas)
    ImportacaoErro.objects.create(
        content_type=content_type,
        object_id=importacao.uuid,
        mensagem='Erro de teste',
        erros='Linha 1: erro na linha 1 | Linha 2: erro na linha 2',
    )
    url = reverse('importacao-arquivo-vagas-download-erros')
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/plain; charset=utf-8'
    assert 'attachment' in resp['Content-Disposition']
    conteudo = resp.content.decode('utf-8')
    assert '**Linha 1:** erro na linha 1' in conteudo
    assert '**Linha 2:** erro na linha 2' in conteudo


def test_download_erros_parte_sem_dois_pontos_apenas_append(api_client):
    """Testa download_erros: partes sem ':' são adicionadas como estão."""
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')
    importacao = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='v.csv',
        arquivo=arquivo,
        tipo='VAGAS',
    )
    content_type = ContentType.objects.get_for_model(ImportacaoArquivoVagas)
    ImportacaoErro.objects.create(
        content_type=content_type,
        object_id=importacao.uuid,
        mensagem='Erro',
        erros='Mensagem simples sem dois pontos',
    )
    url = reverse('importacao-arquivo-vagas-download-erros')
    resp = api_client.get(url)
    assert resp.status_code == 200
    conteudo = resp.content.decode('utf-8')
    assert 'Mensagem simples sem dois pontos' in conteudo


def test_download_erros_filtra_por_importacao_uuid(api_client):
    """Testa download_erros filtra por importacao_uuid quando informado."""
    arquivo = SimpleUploadedFile('v1.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')
    importacao1 = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='v1.csv',
        arquivo=arquivo,
        tipo='VAGAS',
    )
    arquivo2 = SimpleUploadedFile('v2.csv', b'DataFechamentoModulo\n06/09/2025\n', content_type='text/csv')
    importacao2 = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='v2.csv',
        arquivo=arquivo2,
        tipo='VAGAS',
    )
    content_type = ContentType.objects.get_for_model(ImportacaoArquivoVagas)
    ImportacaoErro.objects.create(
        content_type=content_type,
        object_id=importacao1.uuid,
        mensagem='Erro 1',
        erros='Erro importacao 1',
    )
    ImportacaoErro.objects.create(
        content_type=content_type,
        object_id=importacao2.uuid,
        mensagem='Erro 2',
        erros='Erro importacao 2',
    )
    url = reverse('importacao-arquivo-vagas-download-erros')
    resp = api_client.get(url, {'importacao_uuid': str(importacao1.uuid)})
    assert resp.status_code == 200
    conteudo = resp.content.decode('utf-8')
    assert 'Erro importacao 1' in conteudo
    assert 'Erro importacao 2' not in conteudo

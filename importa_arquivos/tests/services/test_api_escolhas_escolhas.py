"""
Testes unitários para métodos relacionados a escolhas no ApiEscolhasService.
"""
import pytest
from unittest.mock import patch, Mock
from requests import RequestException
from requests.exceptions import HTTPError

from importa_arquivos.models import ImportacaoEscolhas, ImportacaoErro
from importa_arquivos.services.api_escolhas import ApiEscolhasService


pytestmark = pytest.mark.django_db


class TestApiEscolhasServiceEscolhasProdam:
    """Testes para métodos de escolhas Prodam no ApiEscolhasService."""

    def test_transformar_escolhas_prodam_para_escolhas_basico(self):
        """Testa transformação básica de dados Prodam para formato MS-Escolhas."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'codigoUnidadeAlocacao': '456789',
                'tipoVaga': 'PRECARIA',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        escolhas = service._transformar_escolhas_prodam_para_escolhas(dados_prodam)
        
        assert len(escolhas) == 1
        assert escolhas[0]['cpf'] == '12345678901'
        assert escolhas[0]['codigo_cargo'] == '123'
        assert escolhas[0]['codigo_eol'] == '456789'
        assert escolhas[0]['tipo_vaga'] == 'PRECARIA'
        assert escolhas[0]['situacao'] == 'ESCOLHA'

    def test_transformar_escolhas_prodam_mapeamento_status_desistente(self):
        """Status DESISTENTE é filtrado (apenas ALOCADO é mantido)."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'DESISTENTE',
            }
        ]
        
        escolhas = service._transformar_escolhas_prodam_para_escolhas(dados_prodam)
        
        assert len(escolhas) == 0

    def test_transformar_escolhas_prodam_mapeamento_status_alocado(self):
        """Testa mapeamento de status ALOCADO para ESCOLHA."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        escolhas = service._transformar_escolhas_prodam_para_escolhas(dados_prodam)
        
        assert escolhas[0]['situacao'] == 'ESCOLHA'

    def test_transformar_escolhas_prodam_status_nao_mapeado(self):
        """Status não mapeados são filtrados (apenas ALOCADO é mantido)."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'OUTRO_STATUS',
            }
        ]
        
        escolhas = service._transformar_escolhas_prodam_para_escolhas(dados_prodam)
        
        assert len(escolhas) == 0

    def test_transformar_escolhas_prodam_campos_opcionais_nulos(self):
        """Testa transformação quando campos opcionais são None."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'codigoUnidadeAlocacao': None,
                'tipoVaga': None,
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        escolhas = service._transformar_escolhas_prodam_para_escolhas(dados_prodam)
        
        assert escolhas[0]['codigo_eol'] == ''
        assert escolhas[0]['tipo_vaga'] == ''

    def test_transformar_escolhas_prodam_multiplos_registros(self):
        """Apenas registros com status ALOCADO são mantidos."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '11111111111',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            },
            {
                'codigoPessoaFisica': '22222222222',
                'codigoCargo': '456',
                'descricaoStatus': 'DESISTENTE',
            },
        ]
        
        escolhas = service._transformar_escolhas_prodam_para_escolhas(dados_prodam)
        
        assert len(escolhas) == 1
        assert escolhas[0]['cpf'] == '11111111111'
        assert escolhas[0]['situacao'] == 'ESCOLHA'

    def test_enviar_escolhas_prodam_sucesso(self):
        """Testa envio bem-sucedido de escolhas Prodam."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        with patch('importa_arquivos.services.api_escolhas.requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp
            
            processo_uuid = '123e4567-e89b-12d3-a456-426614174000'
            concurso_uuid = '223e4567-e89b-12d3-a456-426614174000'
            response = service.enviar_escolhas_prodam(
                processo_uuid=processo_uuid,
                concurso_uuid=concurso_uuid,
                dados_prodam=dados_prodam,
            )
            
            assert response is mock_resp
            args, kwargs = mock_post.call_args
            assert args[0].endswith('/api/v1/escolhas/importacao-prodam/')
            
            payload = kwargs['json']
            assert payload['processo_uuid'] == processo_uuid
            assert payload['concurso_uuid'] == concurso_uuid
            assert 'escolhas' in payload
            assert len(payload['escolhas']) == 1
            assert payload['escolhas'][0]['cpf'] == '12345678901'
            assert payload['escolhas'][0]['situacao'] == 'ESCOLHA'

    def test_enviar_escolhas_prodam_com_headers_customizados(self):
        """Testa envio com headers customizados."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        custom_headers = {'X-Custom-Header': 'custom-value'}
        
        with patch('importa_arquivos.services.api_escolhas.requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp
            
            service.enviar_escolhas_prodam(
                processo_uuid='123e4567-e89b-12d3-a456-426614174000',
                concurso_uuid='223e4567-e89b-12d3-a456-426614174000',
                dados_prodam=dados_prodam,
                headers=custom_headers,
            )
            
            args, kwargs = mock_post.call_args
            merged_headers = kwargs['headers']
            assert 'X-Custom-Header' in merged_headers
            assert merged_headers['X-Custom-Header'] == 'custom-value'
            assert 'Content-Type' in merged_headers
            assert 'Accept' in merged_headers

    def test_enviar_escolhas_prodam_erro_request_exception(self):
        """Testa tratamento de erro RequestException."""
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        with patch('importa_arquivos.services.api_escolhas.requests.post', side_effect=RequestException('Erro de conexão')):
            with pytest.raises(RequestException):
                service.enviar_escolhas_prodam(
                    processo_uuid='123e4567-e89b-12d3-a456-426614174000',
                    concurso_uuid='223e4567-e89b-12d3-a456-426614174000',
                    dados_prodam=dados_prodam,
                )

    def test_enviar_escolhas_prodam_erro_http_parseia_detail_code_detalhes(self):
        """Em erro HTTP, deve parsear detail/code/detalhes da resposta externa."""
        service = ApiEscolhasService(base_url='https://api.exemplo')

        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'detail': 'Erro externo de escolhas',
            'code': 'ERRO_ESCOLHAS',
            'detalhes': 'Payload inválido'
        }
        mock_response.text = '{"detail":"Erro externo de escolhas","code":"ERRO_ESCOLHAS","detalhes":"Payload inválido"}'

        with patch('importa_arquivos.services.api_escolhas.requests.post') as mock_post:
            mock_post.return_value.raise_for_status.side_effect = HTTPError('bad request', response=mock_response)

            with pytest.raises(RequestException) as exc_info:
                service.enviar_escolhas_prodam(
                    processo_uuid='123e4567-e89b-12d3-a456-426614174000',
                    concurso_uuid='223e4567-e89b-12d3-a456-426614174000',
                    dados_prodam=dados_prodam,
                )

            msg = str(exc_info.value)
            assert '"detail": "Erro externo de escolhas"' in msg
            assert '"code": "ERRO_ESCOLHAS"' in msg
            assert '"detalhes": "Payload inválido"' in msg

    def test_enviar_escolhas_prodam_registra_erro_quando_importacao_obj_fornecido(self):
        """Testa que erro é registrado quando importacao_obj é fornecido."""
        importacao = ImportacaoEscolhas.objects.create(
            processo_id=123,
            status='PROCESSANDO',
        )
        
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        with patch('importa_arquivos.services.api_escolhas.requests.post', side_effect=RequestException('Erro de conexão')):
            with pytest.raises(RequestException):
                service.enviar_escolhas_prodam(
                    processo_uuid='123e4567-e89b-12d3-a456-426614174000',
                    concurso_uuid='223e4567-e89b-12d3-a456-426614174000',
                    dados_prodam=dados_prodam,
                    importacao_obj=importacao,
                )
        
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        assert ImportacaoErro.objects.filter(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem='Erro ao enviar escolhas para MS-Escolhas',
        ).exists()

    def test_enviar_escolhas_prodam_nao_quebra_quando_registrar_erro_falha(self):
        """Testa que não quebra quando registrar_erro falha."""
        importacao = ImportacaoEscolhas.objects.create(
            processo_id=123,
            status='PROCESSANDO',
        )
        
        service = ApiEscolhasService(base_url='https://api.exemplo')
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        with patch('importa_arquivos.services.api_escolhas.requests.post', side_effect=RequestException('Erro')):
            with patch('importa_arquivos.services.api_escolhas.registrar_erro', side_effect=RuntimeError('Erro ao registrar')):
                with pytest.raises(RequestException):
                    service.enviar_escolhas_prodam(
                        processo_uuid='123e4567-e89b-12d3-a456-426614174000',
                        concurso_uuid='223e4567-e89b-12d3-a456-426614174000',
                        dados_prodam=dados_prodam,
                        importacao_obj=importacao,
                    )

    def test_enviar_escolhas_prodam_timeout(self):
        """Testa que o timeout é respeitado."""
        service = ApiEscolhasService(base_url='https://api.exemplo', timeout_seconds=60)
        
        dados_prodam = [
            {
                'codigoPessoaFisica': '12345678901',
                'codigoCargo': '123',
                'descricaoStatus': 'ALOCADO',
            }
        ]
        
        with patch('importa_arquivos.services.api_escolhas.requests.post') as mock_post:
            mock_resp = Mock()
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp
            
            service.enviar_escolhas_prodam(
                processo_uuid='123e4567-e89b-12d3-a456-426614174000',
                concurso_uuid='223e4567-e89b-12d3-a456-426614174000',
                dados_prodam=dados_prodam,
            )
            
            args, kwargs = mock_post.call_args
            assert kwargs['timeout'] == 60


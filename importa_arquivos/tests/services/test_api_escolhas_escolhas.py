"""
Testes unitários para métodos relacionados a escolhas no ApiEscolhasService.
"""

from unittest.mock import Mock, patch

import pytest
from requests import RequestException

from importa_arquivos.models import ImportacaoErro, ImportacaoEscolhas
from importa_arquivos.services.api_escolhas import ApiEscolhasService
from importa_arquivos.services.exceptions import ApiEscolhasException

pytestmark = pytest.mark.django_db


class TestApiEscolhasServiceEscolhasProdam:
    """Testes para métodos de escolhas Prodam no ApiEscolhasService."""

    def test_transformar_escolhas_prodam_para_escolhas_basico(self):
        """
        Testa transformação básica de dados Prodam para formato MS-Escolhas.
        """
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "codigoUnidadeAlocacao": "456789",
                "tipoVaga": "PRECARIA",
                "descricaoStatus": "ALOCADO",
            }
        ]

        escolhas = service._transformar_escolhas_prodam_para_escolhas(
            dados_prodam
        )

        assert len(escolhas) == 1
        assert escolhas[0]["cpf"] == "12345678901"
        assert escolhas[0]["codigo_cargo"] == "123"
        assert escolhas[0]["codigo_eol"] == "456789"
        assert escolhas[0]["tipo_vaga"] == "PRECARIA"
        assert escolhas[0]["situacao"] == "ESCOLHA"

    def test_transformar_escolhas_prodam_mapeamento_status_desistente(self):
        """Status DESISTENTE é filtrado (apenas ALOCADO é mantido)."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "DESISTENTE",
            }
        ]

        escolhas = service._transformar_escolhas_prodam_para_escolhas(
            dados_prodam
        )

        assert len(escolhas) == 0

    def test_transformar_escolhas_prodam_mapeamento_status_alocado(self):
        """Testa mapeamento de status ALOCADO para ESCOLHA."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        escolhas = service._transformar_escolhas_prodam_para_escolhas(
            dados_prodam
        )

        assert escolhas[0]["situacao"] == "ESCOLHA"

    def test_transformar_escolhas_prodam_status_nao_mapeado(self):
        """Status não mapeados são filtrados (apenas ALOCADO é mantido)."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "OUTRO_STATUS",
            }
        ]

        escolhas = service._transformar_escolhas_prodam_para_escolhas(
            dados_prodam
        )

        assert len(escolhas) == 0

    def test_transformar_escolhas_prodam_campos_opcionais_nulos(self):
        """Testa transformação quando campos opcionais são None."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "codigoUnidadeAlocacao": None,
                "tipoVaga": None,
                "descricaoStatus": "ALOCADO",
            }
        ]

        escolhas = service._transformar_escolhas_prodam_para_escolhas(
            dados_prodam
        )

        assert escolhas[0]["codigo_eol"] == ""
        assert escolhas[0]["tipo_vaga"] == ""

    def test_transformar_escolhas_prodam_multiplos_registros(self):
        """Apenas registros com status ALOCADO são mantidos."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "11111111111",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            },
            {
                "codigoPessoaFisica": "22222222222",
                "codigoCargo": "456",
                "descricaoStatus": "DESISTENTE",
            },
        ]

        escolhas = service._transformar_escolhas_prodam_para_escolhas(
            dados_prodam
        )

        assert len(escolhas) == 1
        assert escolhas[0]["cpf"] == "11111111111"
        assert escolhas[0]["situacao"] == "ESCOLHA"

    def test_enviar_escolhas_prodam_sucesso(self):
        """Testa envio bem-sucedido de escolhas Prodam."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        with patch("sigla_sdk.http.api_client.http_client.post") as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"ok": True}
            mock_post.return_value = mock_resp

            processo_uuid = "123e4567-e89b-12d3-a456-426614174000"
            concurso_uuid = "223e4567-e89b-12d3-a456-426614174000"
            response = service.enviar_escolhas_prodam(
                processo_uuid=processo_uuid,
                concurso_uuid=concurso_uuid,
                dados_prodam=dados_prodam,
            )

            assert response == {"ok": True}
            args, kwargs = mock_post.call_args
            assert args[0].endswith("/api/v1/escolhas/importacao-prodam/")

            payload = kwargs["json"]
            assert payload["processo_uuid"] == processo_uuid
            assert payload["concurso_uuid"] == concurso_uuid
            assert "escolhas" in payload
            assert len(payload["escolhas"]) == 1
            assert payload["escolhas"][0]["cpf"] == "12345678901"
            assert payload["escolhas"][0]["situacao"] == "ESCOLHA"

    def test_enviar_escolhas_prodam_com_headers_customizados(self):
        """Testa envio com headers customizados."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        custom_headers = {"X-Custom-Header": "custom-value"}

        with patch("sigla_sdk.http.api_client.http_client.post") as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp

            service.enviar_escolhas_prodam(
                processo_uuid="123e4567-e89b-12d3-a456-426614174000",
                concurso_uuid="223e4567-e89b-12d3-a456-426614174000",
                dados_prodam=dados_prodam,
                headers=custom_headers,
            )

            args, kwargs = mock_post.call_args
            merged_headers = kwargs["headers"]
            assert "X-Custom-Header" in merged_headers
            assert merged_headers["X-Custom-Header"] == "custom-value"
            assert "Content-Type" in merged_headers
            assert "Accept" in merged_headers

    def test_enviar_escolhas_prodam_erro_request_exception(self):
        """Testa tratamento de erro RequestException."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        with patch(  # noqa: SIM117
            "sigla_sdk.http.api_client.http_client.post",
            side_effect=RequestException("Erro de conexão"),
        ):
            with pytest.raises(RequestException):
                service.enviar_escolhas_prodam(
                    processo_uuid="123e4567-e89b-12d3-a456-426614174000",
                    concurso_uuid="223e4567-e89b-12d3-a456-426614174000",
                    dados_prodam=dados_prodam,
                )

    def test_enviar_escolhas_prodam_erro_http_levanta_excecao_especifica(self):
        """Em erro HTTP (status != 200), deve levantar ApiEscolhasException."""
        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "detail": "Erro externo de escolhas",
            "code": "ERRO_ESCOLHAS",
            "detalhes": "Payload inválido",
        }
        mock_response.text = '{"detail":"Erro externo de escolhas","code":"ERRO_ESCOLHAS","detalhes":"Payload inválido"}'  # noqa: E501

        with patch("sigla_sdk.http.api_client.http_client.post") as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(ApiEscolhasException) as exc_info:
                service.enviar_escolhas_prodam(
                    processo_uuid="123e4567-e89b-12d3-a456-426614174000",
                    concurso_uuid="223e4567-e89b-12d3-a456-426614174000",
                    dados_prodam=dados_prodam,
                )

            exc = exc_info.value
            assert exc.mensagem == "Falha ao enviar escolhas para API externa"
            assert exc.detalhes == mock_response.text
            assert exc.status_code == 400

    def test_enviar_escolhas_prodam_registra_erro_quando_importacao_obj_fornecido(  # noqa: E501
        self,
    ):
        """Testa que erro é registrado quando importacao_obj é fornecido."""
        importacao = ImportacaoEscolhas.objects.create(
            processo_id=123,
            status="PROCESSANDO",
        )

        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        with patch(  # noqa: SIM117
            "sigla_sdk.http.api_client.http_client.post",
            side_effect=RequestException("Erro de conexão"),
        ):
            with pytest.raises(RequestException):
                service.enviar_escolhas_prodam(
                    processo_uuid="123e4567-e89b-12d3-a456-426614174000",
                    concurso_uuid="223e4567-e89b-12d3-a456-426614174000",
                    dados_prodam=dados_prodam,
                    importacao_obj=importacao,
                )

        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        assert ImportacaoErro.objects.filter(
            content_type=content_type,
            object_id=importacao.uuid,
        ).exists()

    def test_enviar_escolhas_prodam_nao_quebra_quando_registrar_erro_falha(
        self,
    ):
        """Testa que não quebra quando registrar_erro falha."""
        importacao = ImportacaoEscolhas.objects.create(
            processo_id=123,
            status="PROCESSANDO",
        )

        service = ApiEscolhasService(base_url="https://api.exemplo")

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        with patch(  # noqa: SIM117
            "sigla_sdk.http.api_client.http_client.post",
            side_effect=RequestException("Erro"),
        ):
            with patch(
                "importa_arquivos.services.erros.registrar_erro",
                side_effect=RuntimeError("Erro ao registrar"),
            ):
                with pytest.raises(RequestException):
                    service.enviar_escolhas_prodam(
                        processo_uuid="123e4567-e89b-12d3-a456-426614174000",
                        concurso_uuid="223e4567-e89b-12d3-a456-426614174000",
                        dados_prodam=dados_prodam,
                        importacao_obj=importacao,
                    )

    def test_enviar_escolhas_prodam_timeout(self):
        """Testa que o timeout é respeitado."""
        service = ApiEscolhasService(
            base_url="https://api.exemplo", timeout_seconds=60
        )

        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]

        with patch("sigla_sdk.http.api_client.http_client.post") as mock_post:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp

            service.enviar_escolhas_prodam(
                processo_uuid="123e4567-e89b-12d3-a456-426614174000",
                concurso_uuid="223e4567-e89b-12d3-a456-426614174000",
                dados_prodam=dados_prodam,
            )

            args, kwargs = mock_post.call_args
            assert kwargs["timeout"] == 60

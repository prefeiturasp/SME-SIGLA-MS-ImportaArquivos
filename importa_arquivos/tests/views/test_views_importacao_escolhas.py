"""Testes unitários para ImportacaoEscolhasViewSet."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from requests import RequestException

from importa_arquivos.models import ImportacaoErro, ImportacaoEscolhas
from importa_arquivos.services.exceptions import ApiEscolhasException

pytestmark = pytest.mark.django_db


class TestImportacaoEscolhasViewSet:
    """Testes para ImportacaoEscolhasViewSet."""

    def test_create_sucesso_com_dados_prodam(
        self, api_client: Any, settings: Any
    ) -> None:
        """Testa criação bem-sucedida de importação com dados da Prodam."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        resposta_prodam = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [
                {
                    "codigoPessoaFisica": "12345678901",
                    "codigoCargo": "123",
                    "descricaoStatus": "ALOCADO",
                }
            ],
        }
        with (
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiEscolhasService"
            ) as mock_escolhas,
        ):
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.return_value = resposta_prodam  # noqa: E501
            mock_prodam.return_value = mock_prodam_instance
            mock_escolhas_instance = Mock()
            mock_escolhas_instance.enviar_escolhas_prodam.return_value = Mock()
            mock_escolhas.return_value = mock_escolhas_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": processo_id,
                    "concurso_uuid": str(concurso_uuid),
                },
                format="json",
            )
            assert resp.status_code == 201
            assert resp.data["processo_uuid"] == str(processo_uuid)
            assert resp.data["processo_id"] == processo_id
            assert resp.data["status"] == "CONCLUIDO"
            importacao = ImportacaoEscolhas.objects.get(
                processo_uuid=processo_uuid
            )
            assert importacao.status == "CONCLUIDO"
            assert len(importacao.dados_prodam) == 1  # type: ignore[arg-type]

    def test_create_sucesso_com_lista_vazia(
        self, api_client: Any, settings: Any
    ) -> None:
        """Testa criação quando Prodam retorna lista vazia."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        resposta_prodam = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [],
        }
        with patch(
            "importa_arquivos.views.importacao_escolhas.ApiProdamService"
        ) as mock_prodam:
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.return_value = resposta_prodam  # noqa: E501
            mock_prodam.return_value = mock_prodam_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": processo_id,
                    "concurso_uuid": str(concurso_uuid),
                },
                format="json",
            )
            assert resp.status_code == 201
            assert resp.data["status"] == "CONCLUIDO"
            importacao = ImportacaoEscolhas.objects.get(
                processo_uuid=processo_uuid
            )
            assert importacao.status == "CONCLUIDO"

    def test_create_erro_prodam_retorno_false(
        self, api_client: Any, settings: Any
    ) -> None:
        """Testa tratamento quando Prodam retorna retorno=False."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        resposta_prodam = {
            "retorno": "FALSE",
            "mensagem": "Erro na consulta",
            "lstDadosResultadoConvocacaoIngresso": [],
        }
        with patch(
            "importa_arquivos.views.importacao_escolhas.ApiProdamService"
        ) as mock_prodam:
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.return_value = resposta_prodam  # noqa: E501
            mock_prodam.return_value = mock_prodam_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": processo_id,
                    "concurso_uuid": str(concurso_uuid),
                },
                format="json",
            )
            assert resp.status_code == 400
            assert "Erro na API PRODAM" in resp.data["detail"]
            importacao = ImportacaoEscolhas.objects.get(
                processo_uuid=processo_uuid
            )
            assert importacao.status == "ERRO"
            content_type = ContentType.objects.get_for_model(
                ImportacaoEscolhas
            )
            assert ImportacaoErro.objects.filter(
                content_type=content_type,
                object_id=importacao.uuid,
                mensagem="Erro na resposta da API PRODAM",
            ).exists()

    def test_create_erro_ao_consultar_prodam(
        self, api_client: Any, settings: Any
    ) -> None:
        """Testa tratamento de erro ao consultar API Prodam."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        with patch(
            "importa_arquivos.views.importacao_escolhas.ApiProdamService"
        ) as mock_prodam:
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.side_effect = RequestException(  # noqa: E501
                "Erro de conexão"
            )
            mock_prodam.return_value = mock_prodam_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": processo_id,
                    "concurso_uuid": str(concurso_uuid),
                },
                format="json",
            )
            assert resp.status_code == 500
            assert "Erro ao processar importação" in resp.data["detail"]
            importacao = ImportacaoEscolhas.objects.get(
                processo_uuid=processo_uuid
            )
            assert importacao.status == "ERRO"

    def test_create_erro_ao_enviar_para_ms_escolhas(
        self, api_client: Any, settings: Any
    ) -> None:
        """Testa tratamento de erro ao enviar para MS-Escolhas."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        resposta_prodam = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [
                {
                    "codigoPessoaFisica": "12345678901",
                    "codigoCargo": "123",
                    "descricaoStatus": "ALOCADO",
                }
            ],
        }
        with (
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiEscolhasService"
            ) as mock_escolhas,
        ):
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.return_value = resposta_prodam  # noqa: E501
            mock_prodam.return_value = mock_prodam_instance
            mock_escolhas_instance = Mock()
            mock_escolhas_instance.enviar_escolhas_prodam.side_effect = (
                RequestException("Erro ao enviar")
            )
            mock_escolhas.return_value = mock_escolhas_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": processo_id,
                    "concurso_uuid": str(concurso_uuid),
                },
                format="json",
            )
            assert resp.status_code == 500
            assert "Erro ao processar importação" in resp.data["detail"]
            importacao = ImportacaoEscolhas.objects.get(
                processo_uuid=processo_uuid
            )
            assert importacao.status == "ERRO"

    def test_create_erro_ao_enviar_para_ms_escolhas_com_payload_estruturado_retorna_400(  # noqa: E501
        self, api_client: Any, settings: Any
    ) -> None:
        """Quando o serviço externo envia payload estruturado, deve retornar."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        resposta_prodam = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [
                {
                    "codigoPessoaFisica": "12345678901",
                    "codigoCargo": "123",
                    "descricaoStatus": "ALOCADO",
                }
            ],
        }
        with (
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiEscolhasService"
            ) as mock_escolhas,
        ):
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.return_value = resposta_prodam  # noqa: E501
            mock_prodam.return_value = mock_prodam_instance
            mock_escolhas_instance = Mock()
            mock_escolhas_instance.enviar_escolhas_prodam.side_effect = (
                ApiEscolhasException(
                    mensagem="Falha ao enviar escolhas para API externa",
                    detalhes="Candidato não encontrado",
                    status_code=400,
                    code="ERRO_ESCOLHAS",
                )
            )
            mock_escolhas.return_value = mock_escolhas_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": processo_id,
                    "concurso_uuid": str(concurso_uuid),
                },
                format="json",
            )
            assert resp.status_code == 400
            assert (
                resp.data["detail"]
                == "Falha ao enviar escolhas para API externa"
            )
            assert resp.data["detalhes"] == "Candidato não encontrado"
            assert resp.data["code"] == "ERRO_ESCOLHAS"

    def test_create_validacao_serializer_invalido(
        self, api_client: Any
    ) -> None:
        """Testa que dados inválidos retornam erro de validação."""
        url = reverse("importacao-escolhas-list")
        resp = api_client.post(
            url,
            {
                "processo_uuid": "invalid-uuid",
                "processo_id": 123,
                "concurso_uuid": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_list_success(self, api_client: Any) -> None:
        """Testa listagem de importações."""
        processo_uuid1 = uuid.uuid4()
        processo_uuid2 = uuid.uuid4()
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid1, processo_id=123, status="CONCLUIDO"
        )
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid2, processo_id=456, status="ERRO"
        )
        url = reverse("importacao-escolhas-list")
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert "results" in resp.data
        assert len(resp.data["results"]) == 2

    def test_retrieve_success(self, api_client: Any) -> None:
        """Testa recuperação de uma importação específica."""
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid,
            processo_id=123,
            concurso_uuid=concurso_uuid,
            status="CONCLUIDO",
        )
        url = reverse(
            "importacao-escolhas-detail", kwargs={"uuid": importacao.uuid}
        )
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["processo_uuid"] == str(processo_uuid)
        assert resp.data["processo_id"] == 123
        assert resp.data["concurso_uuid"] == str(concurso_uuid)
        assert resp.data["status"] == "CONCLUIDO"

    def test_filterset_processo_uuid(self, api_client: Any) -> None:
        """Testa filtro por processo_uuid."""
        processo_uuid1 = uuid.uuid4()
        processo_uuid2 = uuid.uuid4()
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid1, processo_id=123
        )
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid2, processo_id=456
        )
        url = reverse("importacao-escolhas-list")
        resp = api_client.get(url, {"processo_uuid": str(processo_uuid1)})
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["processo_uuid"] == str(processo_uuid1)

    def test_filterset_status(self, api_client: Any) -> None:
        """Testa filtro por status."""
        processo_uuid1 = uuid.uuid4()
        processo_uuid2 = uuid.uuid4()
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid1, processo_id=123, status="CONCLUIDO"
        )
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid2, processo_id=456, status="ERRO"
        )
        url = reverse("importacao-escolhas-list")
        resp = api_client.get(url, {"status": "CONCLUIDO"})
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["status"] == "CONCLUIDO"

    def test_filterset_processo_id(self, api_client: Any) -> None:
        """Testa filtro por processo_id."""
        processo_uuid1 = uuid.uuid4()
        processo_uuid2 = uuid.uuid4()
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid1, processo_id=123
        )
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid2, processo_id=456
        )
        url = reverse("importacao-escolhas-list")
        resp = api_client.get(url, {"processo_id": 123})
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["processo_id"] == 123

    def test_search_processo_uuid(self, api_client: Any) -> None:
        """Testa busca por processo_uuid."""
        processo_uuid1 = uuid.uuid4()
        processo_uuid2 = uuid.uuid4()
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid1, processo_id=123
        )
        ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid2, processo_id=456
        )
        url = reverse("importacao-escolhas-list")
        resp = api_client.get(url, {"search": str(processo_uuid1)})
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["processo_uuid"] == str(processo_uuid1)

    def test_ordering_criado_em(self, api_client: Any) -> None:
        """Testa ordenação por criado_em."""
        processo_uuid1 = uuid.uuid4()
        processo_uuid2 = uuid.uuid4()
        importacao1 = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid1, processo_id=123
        )
        import time

        time.sleep(0.01)
        importacao2 = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid2, processo_id=456
        )
        url = reverse("importacao-escolhas-list")
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data["results"][0]["uuid"] == str(importacao2.uuid)
        assert resp.data["results"][1]["uuid"] == str(importacao1.uuid)

    def test_get_serializer_class_list(self, api_client: Any) -> None:
        """Testa que get_serializer_class retorna."""
        url = reverse("importacao-escolhas-list")
        resp = api_client.get(url)
        assert resp.status_code == 200
        if resp.data["results"]:
            assert "erros" in resp.data["results"][0]

    def test_get_serializer_class_create(
        self, api_client: Any, settings: Any
    ) -> None:
        """Testa que get_serializer_class retorna."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        resposta_prodam = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [],
        }
        with patch(
            "importa_arquivos.views.importacao_escolhas.ApiProdamService"
        ) as mock_prodam:
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.return_value = resposta_prodam  # noqa: E501
            mock_prodam.return_value = mock_prodam_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": processo_id,
                    "concurso_uuid": str(concurso_uuid),
                },
                format="json",
            )
            assert resp.status_code in [201, 400, 500]

    def test_create_registra_dados_prodam(
        self, api_client: Any, settings: Any
    ) -> None:
        """Testa que dados_prodam são salvos corretamente."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]
        resposta_prodam = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": dados_prodam,
        }
        with (
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.views.importacao_escolhas.ApiEscolhasService"
            ) as mock_escolhas,
        ):
            mock_prodam_instance = Mock()
            mock_prodam_instance.consultar_resultado_convocacao_ingresso.return_value = resposta_prodam  # noqa: E501
            mock_prodam.return_value = mock_prodam_instance
            mock_escolhas_instance = Mock()
            mock_escolhas_instance.enviar_escolhas_prodam.return_value = Mock()
            mock_escolhas.return_value = mock_escolhas_instance
            url = reverse("importacao-escolhas-list")
            resp = api_client.post(
                url,
                {
                    "processo_uuid": str(processo_uuid),
                    "concurso_uuid": str(concurso_uuid),
                    "processo_id": processo_id,
                },
                format="json",
            )
            assert resp.status_code == 201
            importacao = ImportacaoEscolhas.objects.get(
                processo_uuid=processo_uuid
            )
            assert importacao.dados_prodam == dados_prodam

    def test_listar_erros_retorna_lista_vazia_quando_sem_erros(
        self, api_client: Any
    ) -> None:
        """Testa listar_erros retorna lista vazia quando não há erros."""
        url = reverse("importacao-escolhas-listar-erros")
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp.data == []

    def test_listar_erros_retorna_erros_existentes(
        self, api_client: Any
    ) -> None:
        """Testa listar_erros retorna erros de ImportacaoEscolhas."""
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=uuid.uuid4(), processo_id=123, status="ERRO"
        )
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem="Erro de teste",
            erros="Linha 1: erro na linha 1 | Linha 2: erro na linha 2",
        )
        url = reverse("importacao-escolhas-listar-erros")
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["mensagem"] == "Erro de teste"
        assert (
            resp.data[0]["erros"]
            == "Linha 1: erro na linha 1 | Linha 2: erro na linha 2"
        )

    def test_listar_erros_filtra_por_importacao_uuid(
        self, api_client: Any
    ) -> None:
        """Testa listar_erros filtra por importacao_uuid quando informado."""
        importacao1 = ImportacaoEscolhas.objects.create(
            processo_uuid=uuid.uuid4(), processo_id=123, status="ERRO"
        )
        importacao2 = ImportacaoEscolhas.objects.create(
            processo_uuid=uuid.uuid4(), processo_id=456, status="ERRO"
        )
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao1.uuid,
            mensagem="Erro importacao 1",
            erros="Erro 1",
        )
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao2.uuid,
            mensagem="Erro importacao 2",
            erros="Erro 2",
        )
        url = reverse("importacao-escolhas-listar-erros")
        resp = api_client.get(url, {"importacao_uuid": str(importacao1.uuid)})
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["mensagem"] == "Erro importacao 1"
        assert resp.data[0]["erros"] == "Erro 1"

    def test_download_erros_retorna_arquivo_vazio_quando_sem_erros(
        self, api_client: Any
    ) -> None:
        """Testa download_erros retorna arquivo vazio quando não há erros."""
        url = reverse("importacao-escolhas-download-erros")
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/plain; charset=utf-8"
        assert "attachment" in resp["Content-Disposition"]
        assert "escolhas_erros_" in resp["Content-Disposition"]
        assert resp.content == b""

    def test_download_erros_formata_conteudo_corretamente(
        self, api_client: Any
    ) -> None:
        """Testa download_erros formata erros com titulo: conteudo."""
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=uuid.uuid4(), processo_id=123, status="ERRO"
        )
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem="Erro de teste",
            erros="Linha 1: erro na linha 1 | Linha 2: erro na linha 2",
        )
        url = reverse("importacao-escolhas-download-erros")
        resp = api_client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/plain; charset=utf-8"
        assert "attachment" in resp["Content-Disposition"]
        conteudo = resp.content.decode("utf-8")
        assert "**Linha 1:** erro na linha 1" in conteudo
        assert "**Linha 2:** erro na linha 2" in conteudo

    def test_download_erros_parte_sem_dois_pontos_apenas_append(
        self, api_client: Any
    ) -> None:
        """Testa download_erros: partes sem ':' são adicionadas como estão."""
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=uuid.uuid4(), processo_id=123, status="ERRO"
        )
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem="Erro",
            erros="Mensagem simples sem dois pontos",
        )
        url = reverse("importacao-escolhas-download-erros")
        resp = api_client.get(url)
        assert resp.status_code == 200
        conteudo = resp.content.decode("utf-8")
        assert "Mensagem simples sem dois pontos" in conteudo

    def test_download_erros_filtra_por_importacao_uuid(
        self, api_client: Any
    ) -> None:
        """Testa download_erros filtra por importacao_uuid quando informado."""
        importacao1 = ImportacaoEscolhas.objects.create(
            processo_uuid=uuid.uuid4(), processo_id=123, status="ERRO"
        )
        importacao2 = ImportacaoEscolhas.objects.create(
            processo_uuid=uuid.uuid4(), processo_id=456, status="ERRO"
        )
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao1.uuid,
            mensagem="Erro 1",
            erros="Erro importacao 1",
        )
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao2.uuid,
            mensagem="Erro 2",
            erros="Erro importacao 2",
        )
        url = reverse("importacao-escolhas-download-erros")
        resp = api_client.get(url, {"importacao_uuid": str(importacao1.uuid)})
        assert resp.status_code == 200
        conteudo = resp.content.decode("utf-8")
        assert "Erro importacao 1" in conteudo
        assert "Erro importacao 2" not in conteudo

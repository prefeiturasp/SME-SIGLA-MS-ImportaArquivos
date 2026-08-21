"""Testes do serviço de importação de escolhas."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.contrib.contenttypes.models import ContentType
from requests import RequestException

from importa_arquivos.models import ImportacaoErro, ImportacaoEscolhas
from importa_arquivos.models.constants import MODO_IMPORTACAO_AUTOMATICA
from importa_arquivos.services.exceptions import (
    ApiEscolhasError,
    ApiProdamError,
)
from importa_arquivos.services.importacao_escolhas_service import (
    ImportacaoEscolhasService,
)

pytestmark = pytest.mark.django_db


def _payload_prodam(
    itens: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Monta resposta mínima da API PRODAM."""
    return {
        "retorno": "TRUE",
        "mensagem": "Sucesso",
        "lstDadosResultadoConvocacaoIngresso": itens or [],
    }


def _item_prodam() -> dict[str, Any]:
    """Item mínimo retornado pela PRODAM."""
    return {
        "codigoPessoaFisica": "12345678901",
        "codigoCargo": "123",
        "descricaoStatus": "ALOCADO",
    }


class TestImportacaoEscolhasService:
    """Testes de ImportacaoEscolhasService.processar."""

    def test_processar_sucesso_envia_para_ms_escolhas(
        self, settings: Any
    ) -> None:
        """Consulta PRODAM, persiste dados e envia ao MS-Escolhas."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        dados = [_item_prodam()]
        with (
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiEscolhasService"
            ) as mock_escolhas,
        ):
            mock_prodam.return_value.consultar_resultado_convocacao_ingresso.return_value = (  # noqa: E501
                _payload_prodam(dados)
            )
            mock_escolhas.return_value.enviar_escolhas_prodam.return_value = (
                Mock()
            )
            instance = ImportacaoEscolhasService.processar(
                processo_uuid=processo_uuid,
                processo_id=123,
                concurso_uuid=concurso_uuid,
            )
        assert instance.status == "CONCLUIDO"
        assert instance.modo == "MANUAL"
        assert instance.dados_prodam == dados
        mock_escolhas.return_value.enviar_escolhas_prodam.assert_called_once()

    def test_processar_com_modo_automatica(self, settings: Any) -> None:
        """Persiste o modo informado (ex.: disparo pelo Beat)."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        with (
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiEscolhasService"
            ),
        ):
            mock_prodam.return_value.consultar_resultado_convocacao_ingresso.return_value = (  # noqa: E501
                _payload_prodam([])
            )
            instance = ImportacaoEscolhasService.processar(
                processo_uuid=uuid.uuid4(),
                processo_id=123,
                concurso_uuid=uuid.uuid4(),
                modo=MODO_IMPORTACAO_AUTOMATICA,
            )
        assert instance.modo == MODO_IMPORTACAO_AUTOMATICA

    def test_processar_lista_vazia_conclui_sem_enviar(
        self, settings: Any
    ) -> None:
        """Lista vazia da PRODAM conclui sem chamar o MS-Escolhas."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        with (
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiEscolhasService"
            ) as mock_escolhas,
        ):
            mock_prodam.return_value.consultar_resultado_convocacao_ingresso.return_value = (  # noqa: E501
                _payload_prodam([])
            )
            instance = ImportacaoEscolhasService.processar(
                processo_uuid=uuid.uuid4(),
                processo_id=123,
                concurso_uuid=uuid.uuid4(),
            )
        assert instance.status == "CONCLUIDO"
        mock_escolhas.return_value.enviar_escolhas_prodam.assert_not_called()

    def test_processar_erro_prodam_marca_erro_e_registra(
        self, settings: Any
    ) -> None:
        """Retorno FALSE da PRODAM marca ERRO e registra o detalhe."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        with patch(
            "importa_arquivos.services.importacao_escolhas_service.ApiProdamService"
        ) as mock_prodam:
            mock_prodam.return_value.consultar_resultado_convocacao_ingresso.return_value = {  # noqa: E501
                "retorno": "FALSE",
                "mensagem": "Erro na consulta",
                "lstDadosResultadoConvocacaoIngresso": [],
            }
            with pytest.raises(ApiProdamError, match="Erro na API PRODAM"):
                ImportacaoEscolhasService.processar(
                    processo_uuid=processo_uuid,
                    processo_id=123,
                    concurso_uuid=uuid.uuid4(),
                )
        importacao = ImportacaoEscolhas.objects.get(
            processo_uuid=processo_uuid
        )
        assert importacao.status == "ERRO"
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        assert ImportacaoErro.objects.filter(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem="Erro na resposta da API PRODAM",
        ).exists()

    def test_processar_erro_ms_escolhas_marca_erro(
        self, settings: Any
    ) -> None:
        """Falha no MS-Escolhas marca ERRO e relança a exceção."""
        settings.ESCOLHA_API_URL = "https://api.exemplo"
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        with (
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiProdamService"
            ) as mock_prodam,
            patch(
                "importa_arquivos.services.importacao_escolhas_service.ApiEscolhasService"
            ) as mock_escolhas,
        ):
            mock_prodam.return_value.consultar_resultado_convocacao_ingresso.return_value = (  # noqa: E501
                _payload_prodam([_item_prodam()])
            )
            mock_escolhas.return_value.enviar_escolhas_prodam.side_effect = (
                ApiEscolhasError(
                    mensagem="Falha ao enviar",
                    detalhes="Candidato não encontrado",
                    status_code=400,
                    code="ERRO_ESCOLHAS",
                )
            )
            with pytest.raises(ApiEscolhasError, match="Falha ao enviar"):
                ImportacaoEscolhasService.processar(
                    processo_uuid=processo_uuid,
                    processo_id=123,
                    concurso_uuid=uuid.uuid4(),
                )
        importacao = ImportacaoEscolhas.objects.get(
            processo_uuid=processo_uuid
        )
        assert importacao.status == "ERRO"

    def test_processar_request_exception_marca_erro(
        self, settings: Any
    ) -> None:
        """Falha HTTP na PRODAM marca ERRO e relança RequestException."""
        settings.PRODAM_ESCOLHAS_API_URL = "https://api.prodam.com/endpoint"
        settings.PRODAM_API_TOKEN = "token123"
        settings.PRODAM_API_USUARIO = "usuario"
        settings.PRODAM_API_SENHA = "senha"
        processo_uuid = uuid.uuid4()
        with patch(
            "importa_arquivos.services.importacao_escolhas_service.ApiProdamService"
        ) as mock_prodam:
            mock_prodam.return_value.consultar_resultado_convocacao_ingresso.side_effect = (  # noqa: E501
                RequestException("Erro de conexão")
            )
            with pytest.raises(RequestException, match="Erro de conexão"):
                ImportacaoEscolhasService.processar(
                    processo_uuid=processo_uuid,
                    processo_id=123,
                    concurso_uuid=uuid.uuid4(),
                )
        importacao = ImportacaoEscolhas.objects.get(
            processo_uuid=processo_uuid
        )
        assert importacao.status == "ERRO"

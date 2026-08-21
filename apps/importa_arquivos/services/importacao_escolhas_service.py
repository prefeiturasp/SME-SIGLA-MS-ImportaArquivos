"""Serviço de importação de escolhas via PRODAM e MS-Escolhas."""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from requests.exceptions import RequestException

from importa_arquivos.models import ImportacaoEscolhas
from importa_arquivos.models.constants import MODO_IMPORTACAO_MANUAL
from importa_arquivos.repository import ImportacaoEscolhasRepository
from importa_arquivos.services.api_escolhas import ApiEscolhasService
from importa_arquivos.services.api_prodam import ApiProdamService
from importa_arquivos.services.erros import registrar_erro
from importa_arquivos.services.exceptions import (
    ApiEscolhasError,
    ApiProdamError,
)

logger = logging.getLogger(__name__)


class ImportacaoEscolhasService:
    """Orquestra criação, consulta PRODAM e envio ao MS-Escolhas."""

    @classmethod
    def processar(
        cls,
        processo_uuid: Any,
        processo_id: Any,
        concurso_uuid: Any,
        modo: str = MODO_IMPORTACAO_MANUAL,
    ) -> ImportacaoEscolhas:
        """Cria o registro, busca dados na PRODAM e envia ao MS-Escolhas.

        Args:
            processo_uuid: UUID do processo de convocação.
            processo_id: Identificador numérico usado na API PRODAM.
            concurso_uuid: UUID do concurso.
            modo: Disparo da importação (``MANUAL`` ou ``AUTOMATICA``).

        Returns:
            Instância de ``ImportacaoEscolhas`` atualizada.

        Raises:
            ApiProdamError: Quando a PRODAM retorna erro de negócio.
            ApiEscolhasError: Quando o envio ao MS-Escolhas falha.
            RequestException: Quando a chamada HTTP falha.
        """
        instance = ImportacaoEscolhasRepository.criar(
            processo_uuid=processo_uuid,
            processo_id=processo_id,
            concurso_uuid=concurso_uuid,
            status="PROCESSANDO",
            modo=modo,
        )
        try:
            cls._consultar_e_enviar(instance, processo_uuid, concurso_uuid)
        except ApiProdamError:
            raise
        except ApiEscolhasError as exc:
            cls._marcar_erro(
                instance,
                detalhes=exc.detalhes or str(exc),
                exc=exc,
            )
            raise
        except RequestException as exc:
            cls._marcar_erro(instance, detalhes=str(exc), exc=exc)
            raise
        except Exception as exc:
            cls._marcar_erro(instance, detalhes=str(exc), exc=exc)
            raise
        ImportacaoEscolhasRepository.recarregar(instance)
        return instance

    @classmethod
    def _consultar_e_enviar(
        cls,
        instance: ImportacaoEscolhas,
        processo_uuid: Any,
        concurso_uuid: Any,
    ) -> None:
        """Consulta a PRODAM, persiste os dados e envia ao MS-Escolhas."""
        logger.info(
            f"Consultando API externa: processo_id={instance.processo_id}"
        )
        resposta_api = (
            ApiProdamService().consultar_resultado_convocacao_ingresso(
                processo_id=instance.processo_id
            )
        )
        if resposta_api.get("retorno") != "TRUE":
            mensagem_erro = resposta_api.get(
                "mensagem", "Erro desconhecido na API PRODAM"
            )
            logger.error(f"API PRODAM retornou erro: {mensagem_erro}")
            ImportacaoEscolhasRepository.atualizar(instance, status="ERRO")
            registrar_erro(
                instance,
                mensagem="Erro na resposta da API PRODAM",
                detalhes=mensagem_erro,
            )
            raise ApiProdamError(
                mensagem=f"Erro na API PRODAM: {mensagem_erro}",
                detalhes=mensagem_erro,
            )
        dados_prodam = resposta_api.get(
            "lstDadosResultadoConvocacaoIngresso", []
        )
        ImportacaoEscolhasRepository.atualizar(
            instance, dados_prodam=dados_prodam
        )
        if not dados_prodam:
            logger.warning("API PRODAM retornou lista vazia")
            ImportacaoEscolhasRepository.atualizar(
                instance, status="CONCLUIDO"
            )
            return
        logger.info(
            "Enviando %s registros para MS-Escolhas", len(dados_prodam),
            extra={
                "dados_prodam": dados_prodam,
            }
        )
        ApiEscolhasService().enviar_escolhas_prodam(
            processo_uuid=processo_uuid,
            concurso_uuid=concurso_uuid,
            dados_prodam=dados_prodam,
            importacao_obj=instance,
        )
        ImportacaoEscolhasRepository.atualizar(instance, status="CONCLUIDO")
        logger.info(
            f"Importação concluída com sucesso: {len(dados_prodam)} registros"  # noqa: E501
        )

    @staticmethod
    def _marcar_erro(
        instance: ImportacaoEscolhas,
        detalhes: str,
        exc: Exception,
    ) -> None:
        """Marca a importação como erro e registra o detalhe."""
        logger.error(
            f"Erro durante importação de escolhas: {exc}", exc_info=True
        )
        ImportacaoEscolhasRepository.atualizar(instance, status="ERRO")
        with contextlib.suppress(Exception):
            registrar_erro(
                instance,
                mensagem="Erro durante importação de escolhas",
                detalhes=detalhes,
                exc=exc,
            )

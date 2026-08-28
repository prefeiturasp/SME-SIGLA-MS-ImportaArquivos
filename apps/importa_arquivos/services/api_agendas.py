"""Serviço de integração com a API de agendas."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from requests.exceptions import RequestException
from sigla_sdk.http.api_client import http_client

from importa_arquivos.services.exceptions import ApiAgendasError

logger = logging.getLogger(__name__)


class ApiAgendasService:
    """Consulta agendas no MS-Agenda."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            base_url: URL base do serviço remoto.
            timeout_seconds: Tempo máximo de espera pela resposta, em segundos.
        """
        self.base_url = (base_url or settings.AGENDAS_API_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "AGENDAS_API_TIMEOUT", 30
        )
        self._default_headers = {
            "Accept": "application/json",
            settings.API_KEY_HEADER: getattr(
                settings, "AGENDAS_API_KEY", "api-key-agenda"
            ),
        }

    def buscar_por_processo_convocacao_uuid(
        self,
        processo_convocacao_uuid: Any,
    ) -> list[dict[str, Any]]:
        """Lista agendas filtradas por processo de convocação.

        Args:
            processo_convocacao_uuid: UUID do processo de convocação.

        Returns:
            Lista de dicionários da chave ``results`` da API.

        Raises:
            ApiAgendasError: Quando a API falha ou retorna erro.
            RequestException: Quando a chamada HTTP falha.
        """
        url = f"{self.base_url}/api/v1/agendas/"
        params = {"processo_convocacao_uuid": str(processo_convocacao_uuid)}
        logger.info(
            "Buscando agendas por processo_convocacao_uuid=%s",
            processo_convocacao_uuid,
            extra={
                "url": url,
                "method": "GET",
                "params": params,
            },
        )
        try:
            response = http_client.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.error(
                "Erro ao buscar agendas (processo_convocacao_uuid=%s): %s",
                processo_convocacao_uuid,
                exc,
            )
            raise
        if response.status_code >= 400:
            raise ApiAgendasError(
                mensagem="Falha ao buscar agendas",
                detalhes=response.text or f"Status {response.status_code}",
                status_code=response.status_code,
            )
        payload = response.json()
        if isinstance(payload, dict):
            results = payload.get("results") or []
            return [item for item in results if isinstance(item, dict)]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

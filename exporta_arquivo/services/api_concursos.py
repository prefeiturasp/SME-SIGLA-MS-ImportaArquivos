"""Serviço de API para o módulo de concursos.

Consulta detalhes de concurso (código, data de criação) a partir do
concurso_uuid,
usando o MS-Concurso configurado via CONCURSOS_API_URL.
"""

import logging
from typing import Any

from django.conf import settings
from requests.exceptions import RequestException
from sigla_sdk.http.api_client import http_client

from .exceptions import (
    ExportacaoNotFoundException,
    ExportacaoServiceUnavailableException,
)

logger = logging.getLogger(__name__)


class ApiConcursosService:
    """Cliente para a API de concursos (detalhes de concurso)."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            self: Instância do objeto.
            base_url: URL base do serviço remoto.
            timeout_seconds: Tempo máximo de espera pela resposta, em segundos.
        """
        self.base_url = (  # type: ignore[union-attr]
            base_url
            or getattr(settings, "CONCURSOS_API_URL", "http://localhost:8001")
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "CONCURSOS_API_TIMEOUT", 30
        )
        self._default_headers: dict[str, str] = {
            "Accept": "application/json",
        }

    def get_concurso(self, concurso_uuid: str) -> dict[str, Any]:
        """Retorna concurso.

        Args:
            self: Instância do objeto.
            concurso_uuid: UUID do concurso relacionado.

        Returns:
            Dicionário com os dados retornados pela operação.

        Raises:
            ExportacaoNotFoundException: Se ocorrer erro nesta operação.
            ExportacaoServiceUnavailableException: Serviço indisponível.
        """
        url = f"{self.base_url}/api/v1/concursos/{concurso_uuid}/"

        logger.info(f"Chamando API de concursos: {url}")

        try:
            response = http_client.get(
                url,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.exception("Erro ao chamar API de concursos: %s", exc)
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de concursos indisponível.",
                detalhes=str(exc),
            ) from exc

        if response.status_code == 404:
            logger.error(f"Concurso não encontrado: {url}")
            raise ExportacaoNotFoundException(
                mensagem="Concurso não encontrado.",
                detalhes=f"concurso_uuid={concurso_uuid}",
            )

        if response.status_code >= 500:
            logger.error(
                "API concursos retornou status %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de concursos indisponível.",
                detalhes=f"Status {response.status_code}",
            )

        if response.status_code != 200:
            logger.error(f"Erro ao obter dados do concurso: {url}")
            raise ExportacaoServiceUnavailableException(
                mensagem="Erro ao obter dados do concurso.",
                detalhes=f"Status {response.status_code}",
            )

        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("Resposta da API de concursos não é JSON válido.")
            raise ExportacaoServiceUnavailableException(
                mensagem="Resposta inválida do serviço de concursos.",
                detalhes=str(exc),
            ) from exc

        if not isinstance(data, dict):
            raise ExportacaoServiceUnavailableException(
                mensagem="Resposta inválida do serviço de concursos.",
                detalhes="Esperado objeto JSON.",
            )

        return data

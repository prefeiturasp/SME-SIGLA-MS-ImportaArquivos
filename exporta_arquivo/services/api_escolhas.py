"""Serviço de API para o módulo de escolhas (vagas-escolas).

Faz GET em vagas-escolas com processo_uuid e cargo_codigo.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from requests.exceptions import RequestException
from sigla_sdk.http.api_client import http_client

from .exceptions import EscolhasServiceUnavailableException

logger = logging.getLogger(__name__)


class ApiEscolhasService:
    """Cliente para a API de escolhas (GET vagas-escolas)."""

    def __init__(
        self, base_url: str | None = None, timeout_seconds: int | None = None
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            base_url: URL base do serviço remoto.
            timeout_seconds: Tempo máximo de espera pela resposta, em segundos.
        """
        self.base_url = (
            base_url
            or getattr(settings, "ESCOLHA_API_URL", "http://localhost:8004")
        ).rstrip("/")  # type: ignore[union-attr]
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "ESCOLHA_API_TIMEOUT", 30
        )
        self._default_headers = {"Accept": "application/json"}

    def get_vagas_escolas(
        self, processo_uuid: str, cargo_codigo: str | int
    ) -> dict[str, Any]:
        """Retorna vagas escolas.

        Args:
            processo_uuid: UUID do processo de convocação.
            cargo_codigo: Código numérico do cargo.

        Returns:
            Dicionário com os dados processados.

        Raises:
            EscolhasServiceUnavailableException: Serviço indisponível.
        """
        url = f"{self.base_url}/api/v1/vagas-escolas/"
        params = {
            "processo_uuid": processo_uuid,
            "cargo_codigo": str(cargo_codigo),
        }
        try:
            response = http_client.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.exception(
                "Erro ao chamar API de escolha (vagas-escolas): %s", exc
            )
            raise EscolhasServiceUnavailableException(
                mensagem="Serviço de vagas por escola indisponível.",
                detalhes=str(exc),
            ) from exc
        if response.status_code >= 500:
            logger.error(
                "API escolha retornou status %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise EscolhasServiceUnavailableException(
                mensagem="Serviço de vagas por escola indisponível.",
                detalhes=f"Status {response.status_code}",
            )
        if response.status_code != 200:
            raise EscolhasServiceUnavailableException(
                mensagem="Erro ao obter vagas por escola.",
                detalhes=f"Status {response.status_code}",
            )
        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("Resposta da API de escolha não é JSON válido.")
            raise EscolhasServiceUnavailableException(
                mensagem="Resposta inválida do serviço de vagas.",
                detalhes=str(exc),
            ) from exc
        if not isinstance(data, dict):
            raise EscolhasServiceUnavailableException(
                mensagem="Resposta inválida do serviço de vagas.",
                detalhes="Esperado objeto JSON.",
            )
        return data

    def get_escolhas(
        self, candidato_uuids: list[str], concurso_uuid: str
    ) -> list[dict[str, Any]]:
        """Retorna escolhas.

        Args:
            candidato_uuids: UUIDs dos candidatos consultados.
            concurso_uuid: UUID do concurso relacionado.

        Returns:
            Lista com os registros obtidos.

        Raises:
            EscolhasServiceUnavailableException: Serviço indisponível.
        """
        url = f"{self.base_url}/api/v1/escolhas/busca/"
        payload = {
            "candidato_uuid": [str(u) for u in candidato_uuids],
            "concurso_uuid": str(concurso_uuid),
        }
        try:
            response = http_client.post(
                url,
                json=payload,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.exception(
                "Erro ao chamar API de escolhas (busca lote): %s", exc
            )
            raise EscolhasServiceUnavailableException(
                mensagem="Serviço de escolhas indisponível.", detalhes=str(exc)
            ) from exc
        if response.status_code >= 500:
            logger.error(
                "API escolhas retornou status %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise EscolhasServiceUnavailableException(
                mensagem="Serviço de escolhas indisponível.",
                detalhes=f"Status {response.status_code}",
            )
        if response.status_code != 200:
            raise EscolhasServiceUnavailableException(
                mensagem="Erro ao obter escolhas do lote.",
                detalhes=f"Status {response.status_code}",
            )
        return response.json()  # type: ignore[no-any-return]

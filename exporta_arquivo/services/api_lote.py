"""Serviço de API para exportação de lotes.

Contém dois clientes:
- ApiLoteCandidatosService: busca candidatos de um lote específico via
MS-Candidatos.
- ApiLoteEscolhasService: busca escolhas de uma lista de candidatos via
MS-Escolhas,
  filtrando por concurso_uuid.
"""

from __future__ import annotations

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


class ApiLoteCandidatosService:
    """Busca todos os ConcursoCandidato de um lote específico (por lote."""

    def __init__(
        self, base_url: str | None = None, timeout_seconds: int | None = None
    ) -> None:
        """Executa   init  .

        Args:
            self: Instância do objeto.
            base_url: Parâmetro base url.
            timeout_seconds: Parâmetro timeout seconds.

        Raises:
            Nenhuma exceção específica documentada.
        """
        self.base_url = (
            base_url
            or getattr(settings, "CANDIDATOS_API_URL", "http://localhost:8000")
        ).rstrip("/")  # type: ignore[union-attr]
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "CANDIDATOS_API_TIMEOUT", 30
        )
        self._default_headers = {"Accept": "application/json"}

    def _fazer_request_get(
        self, url: str, params: dict, descricao_contexto: str
    ) -> list[dict[str, Any]]:
        """Método comum para realizar requisições GET padronizadas na API de.

        Args:
            self: Instância do objeto.
            url: Parâmetro url.
            params: Parâmetro params.
            descricao_contexto: Parâmetro descricao contexto.

        Returns:
            Lista com os registros resultantes.

        Raises:
            ExportacaoNotFoundException: Se ocorrer erro nesta operação.
            ExportacaoServiceUnavailableException: Fixture do teste.
        """
        try:
            response = http_client.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.exception(
                "Erro ao chamar API de candidatos (%s): %s",
                descricao_contexto,
                exc,
            )
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de candidatos indisponível.",
                detalhes=str(exc),
            ) from exc
        if response.status_code == 404:
            raise ExportacaoNotFoundException(
                mensagem=f"Dados não encontrados ({descricao_contexto}).",
                detalhes=f"Parâmetros: {params}",
            )
        if response.status_code >= 500:
            logger.error(
                "API candidatos retornou status %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de candidatos indisponível.",
                detalhes=f"Status {response.status_code}",
            )
        if response.status_code != 200:
            raise ExportacaoServiceUnavailableException(
                mensagem=f"Erro ao obter dados: {descricao_contexto}.",
                detalhes=f"Status {response.status_code}",
            )
        try:
            data = response.json()
        except ValueError as exc:
            logger.exception(
                "Resposta da API de candidatos não é JSON válido."
            )
            raise ExportacaoServiceUnavailableException(
                mensagem="Resposta inválida do serviço de candidatos.",
                detalhes=str(exc),
            ) from exc
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            return results if isinstance(results, list) else []
        return []

    def get_candidatos_lote(self, lote_uuid: str) -> list[dict[str, Any]]:
        """GET {CANDIDATOS_API_URL}/api/v1/habilitados/?lote__uuid=<uuid>.

        Args:
            self: Instância do objeto.
            lote_uuid: Parâmetro lote uuid.

        Returns:
            Lista com os registros resultantes.

        Raises:
            Nenhuma exceção específica documentada.
        """
        url = f"{self.base_url}/api/v1/habilitados/"
        params = {"lote__uuid": str(lote_uuid)}
        return self._fazer_request_get(url, params, "lote")

    def get_candidatos_por_numero_lote(
        self, concurso_uuid: str, numero_lote: int
    ) -> list[dict[str, Any]]:
        """GET.

        Args:
            self: Instância do objeto.
            concurso_uuid: Parâmetro concurso uuid.
            numero_lote: Parâmetro numero lote.

        Returns:
            Lista com os registros resultantes.

        Raises:
            Nenhuma exceção específica documentada.
        """
        url = f"{self.base_url}/api/v1/habilitados/"
        params: dict[str, Any] = {
            "lote__concurso_uuid": str(concurso_uuid),
            "numero_lote": numero_lote,
        }
        return self._fazer_request_get(url, params, "numero_lote")


class ApiLoteEscolhasService:
    """Busca escolhas para uma lista de candidatos filtradas por."""

    def __init__(
        self, base_url: str | None = None, timeout_seconds: int | None = None
    ) -> None:
        """Executa   init  .

        Args:
            self: Instância do objeto.
            base_url: Parâmetro base url.
            timeout_seconds: Parâmetro timeout seconds.

        Raises:
            Nenhuma exceção específica documentada.
        """
        self.base_url = (
            base_url
            or getattr(settings, "ESCOLHA_API_URL", "http://localhost:8004")
        ).rstrip("/")  # type: ignore[union-attr]
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "ESCOLHA_API_TIMEOUT", 30
        )
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_escolhas_lote(
        self, candidato_uuids: list[str], concurso_uuid: str
    ) -> list[dict[str, Any]]:
        """POST {ESCOLHA_API_URL}/api/v1/escolhas/busca/.

        Args:
            self: Instância do objeto.
            candidato_uuids: Parâmetro candidato uuids.
            concurso_uuid: Parâmetro concurso uuid.

        Returns:
            Lista com os registros resultantes.

        Raises:
            ExportacaoServiceUnavailableException: em 5xx, timeout ou resposta.
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
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de escolhas indisponível.", detalhes=str(exc)
            ) from exc
        if response.status_code >= 500:
            logger.error(
                "API escolhas retornou status %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de escolhas indisponível.",
                detalhes=f"Status {response.status_code}",
            )
        if response.status_code != 200:
            raise ExportacaoServiceUnavailableException(
                mensagem="Erro ao obter escolhas do lote.",
                detalhes=f"Status {response.status_code}",
            )
        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("Resposta da API de escolhas não é JSON válido.")
            raise ExportacaoServiceUnavailableException(
                mensagem="Resposta inválida do serviço de escolhas.",
                detalhes=str(exc),
            ) from exc
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
            return results if isinstance(results, list) else []
        return []

"""
Serviço de API para o módulo de candidatos (habilitados).

Faz GET em habilitados com processo_uuid, codigo_cargo e opcionalmente lote__concurso_uuid.
"""
import logging
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

from django.conf import settings

from .exceptions import ExportacaoNotFoundException, ExportacaoServiceUnavailableException

logger = logging.getLogger(__name__)


class ApiCandidatosService:
    """Cliente para a API de candidatos (GET habilitados)."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.base_url = (base_url or getattr(settings, 'CANDIDATOS_API_URL', 'http://localhost:8000')).rstrip('/')
        self.timeout_seconds = timeout_seconds or getattr(settings, 'CANDIDATOS_API_TIMEOUT', 30)
        self._default_headers = {
            'Accept': 'application/json',
        }

    def get_habilitados(
        self,
        processo_uuid: str,
        codigo_cargo: str | int,
        lote__concurso_uuid: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        GET {CANDIDATOS_API_URL}/api/v1/habilitados/ com query params processo_uuid, codigo_cargo
        e opcionalmente lote__concurso_uuid. Retorna a lista de habilitados.

        A API pode retornar lista direta ou objeto paginado com 'results'; este método
        normaliza para sempre retornar uma lista.

        Raises:
            ExportacaoNotFoundException: Em 404.
            ExportacaoServiceUnavailableException: Em 5xx, timeout ou resposta não-JSON.
        """
        url = f"{self.base_url}/api/v1/habilitados/"
        params = {
            'processo_uuid': processo_uuid,
            'codigo_cargo': str(codigo_cargo),
        }
        if lote__concurso_uuid:
            params['lote__concurso_uuid'] = lote__concurso_uuid

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.exception("Erro ao chamar API de habilitados: %s", exc)
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de candidatos (habilitados) indisponível.",
                detalhes=str(exc),
            ) from exc

        if response.status_code == 404:
            raise ExportacaoNotFoundException(
                mensagem="Recurso de habilitados não encontrado.",
                detalhes="Habilitados não encontrado.",
            )

        if response.status_code >= 500:
            logger.error(
                "API candidatos (habilitados) retornou status %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de candidatos (habilitados) indisponível.",
                detalhes=f"Status {response.status_code}",
            )

        if response.status_code != 200:
            raise ExportacaoServiceUnavailableException(
                mensagem="Erro ao obter habilitados.",
                detalhes=f"Status {response.status_code}",
            )

        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("Resposta da API de habilitados não é JSON válido.")
            raise ExportacaoServiceUnavailableException(
                mensagem="Resposta inválida do serviço de candidatos.",
                detalhes=str(exc),
            ) from exc

        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'results' in data:
            results = data['results']
            return results if isinstance(results, list) else []
        return []

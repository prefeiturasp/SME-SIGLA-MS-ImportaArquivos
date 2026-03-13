"""
Serviço de API para o módulo de escolhas (vagas-escolas).

Faz GET em vagas-escolas com processo_uuid e cargo_codigo.
"""
import logging
from typing import Any, Dict

import requests
from requests.exceptions import RequestException

from django.conf import settings

from .exceptions import ExportacaoServiceUnavailableException

logger = logging.getLogger(__name__)


class ApiEscolhasService:
    """Cliente para a API de escolhas (GET vagas-escolas)."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.base_url = (base_url or getattr(settings, 'ESCOLHA_API_URL', 'http://localhost:8004')).rstrip('/')
        self.timeout_seconds = timeout_seconds or getattr(settings, 'ESCOLHA_API_TIMEOUT', 30)
        self._default_headers = {
            'Accept': 'application/json',
        }

    def get_vagas_escolas(
        self,
        processo_uuid: str,
        cargo_codigo: str | int,
    ) -> Dict[str, Any]:
        """
        GET {ESCOLHA_API_URL}/api/v1/vagas-escolas/ com query params processo_uuid e cargo_codigo.
        Retorna o corpo da resposta (dict, ex.: com chave 'vagas').

        Raises:
            ExportacaoServiceUnavailableException: Em 5xx, timeout ou resposta não-JSON.
        """
        url = f"{self.base_url}/api/v1/vagas-escolas/"
        params = {
            'processo_uuid': processo_uuid,
            'cargo_codigo': str(cargo_codigo),
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.exception("Erro ao chamar API de escolha (vagas-escolas): %s", exc)
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de vagas por escola indisponível.",
                detalhes=str(exc),
            ) from exc

        if response.status_code >= 500:
            logger.error(
                "API escolha retornou status %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise ExportacaoServiceUnavailableException(
                mensagem="Serviço de vagas por escola indisponível.",
                detalhes=f"Status {response.status_code}",
            )

        if response.status_code != 200:
            raise ExportacaoServiceUnavailableException(
                mensagem="Erro ao obter vagas por escola.",
                detalhes=f"Status {response.status_code}",
            )

        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("Resposta da API de escolha não é JSON válido.")
            raise ExportacaoServiceUnavailableException(
                mensagem="Resposta inválida do serviço de vagas.",
                detalhes=str(exc),
            ) from exc

        if not isinstance(data, dict):
            raise ExportacaoServiceUnavailableException(
                mensagem="Resposta inválida do serviço de vagas.",
                detalhes="Esperado objeto JSON.",
            )

        return data

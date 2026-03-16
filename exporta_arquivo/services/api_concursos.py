"""
Serviço de API para o módulo de concursos.

Consulta detalhes de concurso (código, data de criação) a partir do concurso_uuid,
usando o MS-Concurso configurado via CONCURSOS_API_URL.
"""
import logging
from typing import Any, Dict, Optional, Tuple

import requests
from requests.exceptions import RequestException

from django.conf import settings

from .exceptions import ExportacaoNotFoundException, ExportacaoServiceUnavailableException

logger = logging.getLogger(__name__)


class ApiConcursosService:
    """Cliente para a API de concursos (detalhes de concurso)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> None:
        self.base_url = (base_url or getattr(settings, "CONCURSOS_API_URL", "http://localhost:8001")).rstrip("/")
        self.timeout_seconds = timeout_seconds or getattr(settings, "CONCURSOS_API_TIMEOUT", 30)
        self._default_headers: Dict[str, str] = {
            "Accept": "application/json",
        }

    def get_concurso(self, concurso_uuid: str) -> Dict[str, Any]:
        """
        GET {CONCURSOS_API_URL}/api/v1/concursos/{concurso_uuid}/

        Espera um objeto JSON com, pelo menos, os campos:
        - codigo
        - data_criacao

        Raises:
            ExportacaoNotFoundException: em 404.
            ExportacaoServiceUnavailableException: em timeout, 5xx ou resposta inválida.
        """
        url = f"{self.base_url}/api/v1/concursos/{concurso_uuid}/"

        try:
            response = requests.get(
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


_api_concursos = ApiConcursosService()


def buscar_dados_concurso(concurso_uuid: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Consulta MS-Concurso e retorna (concurso_codigo, concurso_data_criacao_iso)
    ou (None, None) em caso de não encontrado.

    As exceções de indisponibilidade (timeout/5xx/resposta inválida) são propagadas
    como ExportacaoServiceUnavailableException.
    """
    try:
        data = _api_concursos.get_concurso(concurso_uuid)
    except ExportacaoNotFoundException:
        # Sem dados de concurso: não aborta, apenas não preenche
        return None, None

    codigo_raw = data.get("codigo")
    try:
        codigo: Optional[int] = int(codigo_raw) if codigo_raw is not None else None
    except (TypeError, ValueError):
        codigo = None

    # Tenta várias chaves possíveis para a data de criação, para tolerar diferenças na API.
    data_criacao = (
        data.get("data_criacao")
        or data.get("dataCriacao")
        or data.get("criado_em")
        or data.get("criadoEm")
    )
    if isinstance(data_criacao, str):
        data_criacao_str: Optional[str] = data_criacao.strip() or None
    else:
        data_criacao_str = None

    return codigo, data_criacao_str


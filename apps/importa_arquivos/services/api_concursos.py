"""Módulo services/api_concursos."""

from __future__ import annotations

import logging

from django.conf import settings
from requests.exceptions import RequestException
from sigla_sdk.http.api_client import http_client

from importa_arquivos.services.exceptions import CargoConcursoInvalidoException

logger = logging.getLogger(__name__)


class ApiConcursosService:
    """Serviço para operações de apiconcursos."""

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
        self.base_url = (
            base_url
            or getattr(settings, "CONCURSOS_API_URL", "http://localhost:8001")
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "CONCURSOS_API_TIMEOUT", 10
        )
        self._default_headers = {
            "Accept": "application/json",
            settings.API_KEY_HEADER: settings.CONCURSOS_API_KEY,
        }

    def obter_codigos_cargo_do_concurso(self, concurso_uuid: str) -> set[int]:
        """Obtém codigos cargo do concurso.

        Args:
            concurso_uuid: UUID do concurso relacionado.

        Returns:
            Conjunto de códigos inteiros dos cargos vinculados ao concurso.

        Raises:
            CargoConcursoInvalidoException: Quando o concurso é inválido ou
                a API está indisponível.
        """
        url = f"{self.base_url}/api/v1/concursos/{concurso_uuid}/"
        try:
            response = http_client.get(
                url,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.error("Erro ao consultar concursos API: %s", exc)
            raise CargoConcursoInvalidoException(
                mensagem="Serviço de concursos indisponível.",
                detalhes=str(exc),
            ) from exc
        if response.status_code == 404:
            raise CargoConcursoInvalidoException(
                mensagem="Concurso não encontrado.",
                detalhes=f"Concurso UUID '{concurso_uuid}' não encontrado na API de concursos.",  # noqa: E501
            )
        if response.status_code >= 500:
            raise CargoConcursoInvalidoException(
                mensagem="Serviço de concursos indisponível.",
                detalhes=f"Status {response.status_code} ao consultar concurso '{concurso_uuid}'.",  # noqa: E501
            )
        cargos = response.json().get("cargos", [])
        return {
            int(cargo["codigo"])
            for cargo in cargos
            if cargo.get("codigo") is not None
        }

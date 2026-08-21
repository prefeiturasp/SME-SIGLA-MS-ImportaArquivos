"""Serviço de integração com a API de processos de convocação."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from requests.exceptions import RequestException
from sigla_sdk.http.api_client import http_client

from importa_arquivos.services.exceptions import ApiProcessosConvocacaoError

logger = logging.getLogger(__name__)

STATUS_PENDENTE = "PENDENTE"
PROCESSO_ID_PRODAM_PADRAO = 819


class ApiProcessosConvocacaoService:
    """Consulta processos de convocação no MS-Processos."""

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
            base_url or settings.PROCESSOS_CONVOCACAO_API_URL
        ).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds
            or getattr(settings, "PROCESSOS_CONVOCACAO_API_TIMEOUT", 30)
        )
        self._default_headers = {
            "Accept": "application/json",
            settings.API_KEY_HEADER: getattr(
                settings,
                "PROCESSOS_CONVOCACAO_API_KEY",
                "api-key-processos-convocacao",
            ),
        }

    def listar_pendentes(self) -> list[dict[str, Any]]:
        """Lista processos com status ``PENDENTE``.

        Returns:
            Lista de dicionários da chave ``results`` da API.

        Raises:
            ApiProcessosConvocacaoError: Quando a API falha ou retorna erro.
            RequestException: Quando a chamada HTTP falha.
        """
        url = f"{self.base_url}/api/v1/processos-convocacao/"
        params: dict[str, Any] = {"status": STATUS_PENDENTE}
        resultados: list[dict[str, Any]] = []
        logger.info(f"Listando processos de convocação pendentes",
            extra={
                "url": url,
                "method": "GET",
                "params": params,
                "headers": self._default_headers,
                "timeout": self.timeout_seconds,
            })
        try:
            response = http_client.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.error(
                "Erro ao listar processos de convocação pendentes: %s", exc
            )
            raise
        if response.status_code >= 400:
            logger.error(f"Erro ao listar processos de convocação pendentes:",
                extra={
                    "url": url,
                    "method": "GET",
                    "params": params,
                    "status": response.status_code,
                    "response": response.text,
                    "error": exc,
                })
            raise ApiProcessosConvocacaoError(
                mensagem="Falha ao listar processos de convocação pendentes",
                detalhes=response.text
                or f"Status {response.status_code}",
                status_code=response.status_code,
            )
        payload = response.json()
        if isinstance(payload, dict):
            pagina = payload.get("results") or []
            if isinstance(pagina, list):
                resultados.extend(
                    item for item in pagina if isinstance(item, dict)
                )
            url = payload.get("next")
            params = {}
        elif isinstance(payload, list):
            resultados.extend(
                item for item in payload if isinstance(item, dict)
            )

        logger.info(
            "Processos PENDENTES encontrados: %s", len(resultados)
        )
        return resultados

    @staticmethod
    def extrair_processo_uuid_e_id(
        processos: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Extrai ``processo_uuid``, ``processo_id`` e ``concurso_uuid``.

        A API retorna ``uuid`` / ``concurso_uuid``. O ``processo_id`` da
        PRODAM só é usado se vier no payload; caso contrário cai no
        padrão histórico (819).

        Args:
            processos: Itens retornados por ``listar_pendentes``.

        Returns:
            Lista com ``processo_uuid``, ``processo_id`` e
            ``concurso_uuid``.
        """
        extraidos: list[dict[str, Any]] = []
        vistos: set[tuple[str, int]] = set()
        for item in processos:
            processo_uuid = item.get("processo_uuid") or item.get("uuid")
            concurso_uuid = item.get("concurso_uuid")
            if not processo_uuid or not concurso_uuid:
                continue
            processo_id = item.get("processo_id")
            if processo_id is None:
                processo_id = PROCESSO_ID_PRODAM_PADRAO
            chave = (str(processo_uuid), int(processo_id))
            if chave in vistos:
                continue
            vistos.add(chave)
            extraidos.append(
                {
                    "processo_uuid": str(processo_uuid),
                    "processo_id": int(processo_id),
                    "concurso_uuid": str(concurso_uuid),
                }
            )
        return extraidos

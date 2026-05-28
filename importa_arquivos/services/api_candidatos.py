"""
Serviços para integração com API de candidatos.
"""

import json
import logging
from typing import Any

from requests import RequestException, Response
from requests.exceptions import RequestException  # noqa: F811
from sigla_sdk.http.api_client import http_client

from importa_arquivos.services.erros import (
    captura_erros_importacao,
)
from importa_arquivos.services.exceptions import (
    ApiCandidatosException,
    ImportacaoBadRequestException,
    ImportacaoServiceUnavailableException,
)

logger = logging.getLogger(__name__)


class ApiCandidatosService:
    def __init__(
        self, base_url: str = "https://example.com", timeout_seconds: int = 30
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _transformar_registros(
        self, registros: list[dict[str, Any]], estrutura: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Transforma os registros do CSV para o formato esperado pela API.
        """
        mapa_coluna_para_payload: dict[str, str] = {}
        for item in estrutura:
            if not isinstance(item, dict):
                continue
            coluna = item.get("coluna")
            campo_payload = item.get("campo_payload")
            if coluna and campo_payload:
                mapa_coluna_para_payload[str(coluna)] = str(campo_payload)

        transformados: list[dict[str, Any]] = []
        for row in registros:
            novo: dict[str, Any] = {}
            for coluna_original, valor in row.items():
                nome_payload = mapa_coluna_para_payload.get(coluna_original)
                if not nome_payload:
                    continue
                novo[nome_payload] = valor
            transformados.append(novo)
        return transformados

    @captura_erros_importacao(param_nome_obj="importacao_obj")
    def enviar_habilitados(
        self,
        registros: list[dict[str, Any]],
        estrutura: list[dict[str, Any]],
        concurso_uuid: str,
        concurso_nome: str,
        headers: dict[str, str] | None = None,
        importacao_obj: Any | None = None,
    ) -> Response:
        url = f"{self.base_url}/api/v1/candidatos/"
        merged_headers = {**self._default_headers, **(headers or {})}

        dados_transformados = self._transformar_registros(registros, estrutura)

        payload = {
            "concurso_uuid": concurso_uuid,
            "concurso_nome": concurso_nome,
            "candidatos": dados_transformados,
        }
        try:
            response = http_client.post(
                url,
                json=payload,
                headers=merged_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.error("Erro ao enviar candidatos: %s", exc)
            raise

        if response.status_code >= 400:
            raise ApiCandidatosException(
                mensagem="Falha ao enviar candidatos para API externa",
                detalhes=response.text or f"Status {response.status_code}",
                status_code=response.status_code,
            )

        logger.info(
            "Candidatos enviados: %s (concurso=%s)",
            len(dados_transformados),
            concurso_uuid,
        )
        return response.json()

    @captura_erros_importacao(param_nome_obj="importacao_obj")
    def salvar_lotes(
        self, concurso_uuid: str, lotes: list, importacao_obj=None
    ) -> int:
        """
        POST {base_url}/api/v1/habilitados/salvar-lotes/

        Retorna o total de candidatos atualizados.

        Raises:
            ImportacaoBadRequestException: Em 400.
            ImportacaoServiceUnavailableException: Em 5xx, timeout ou resposta
            não-JSON.
        """
        url = f"{self.base_url}/api/v1/habilitados/salvar-lotes/"
        payload = {
            "concurso_uuid": concurso_uuid,
            "lotes": lotes,
        }

        try:
            response = http_client.post(
                url,
                json=payload,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.exception("Erro ao chamar API salvar-lotes: %s", exc)
            raise ImportacaoServiceUnavailableException(
                mensagem="Serviço de candidatos (salvar-lotes) indisponível.",
                detalhes=str(exc),
            ) from exc

        if response.status_code == 400:
            logger.error(
                "API salvar-lotes retornou status %s: %s",
                response.status_code,
                response.text,
            )
            mensagem = "Erro na requisição ao salvar lotes."
            detail = mensagem
            try:
                payload_erro = response.json()
                mensagem = payload_erro.get("mensagem", mensagem)
                detail = payload_erro.get("detail", mensagem)
            except (ValueError, json.JSONDecodeError):
                detail = "Erro JSONDecodeError"

            raise ImportacaoBadRequestException(
                mensagem=mensagem, detalhes=detail
            )

        if response.status_code >= 500:
            logger.error(
                "API salvar-lotes retornou status %s: %s",
                response.status_code,
                response.text,
            )
            raise ImportacaoServiceUnavailableException(
                mensagem="Serviço de candidatos (salvar-lotes) indisponível.",
                detalhes=f"Status {response.status_code}: {response.text}",
            )

        if response.status_code not in (200, 201):
            logger.error(
                "API salvar-lotes retornou status %s: %s",
                response.status_code,
                response.text,
            )
            raise ImportacaoServiceUnavailableException(
                mensagem="Erro ao salvar lotes.",
                detalhes=f"Status {response.status_code}: {response.text}",
            )

        return int(response.json().get("total_atualizados", 0))

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

    def __init__(self, base_url: str | None=None, timeout_seconds: int | None=None) -> None:
        """Executa   init  ."""
        self.base_url = (base_url or getattr(settings, 'ESCOLHA_API_URL', 'http://localhost:8004')).rstrip('/')  # type: ignore[union-attr]
        self.timeout_seconds = timeout_seconds or getattr(settings, 'ESCOLHA_API_TIMEOUT', 30)
        self._default_headers = {'Accept': 'application/json'}

    def get_vagas_escolas(self, processo_uuid: str, cargo_codigo: str | int) -> dict[str, Any]:
        """GET {ESCOLHA_API_URL}/api/v1/vagas-escolas/ com query params.

        processo_uuid e cargo_codigo.
        Retorna o corpo da resposta (dict, ex.: com chave 'vagas').

        Raises:
            EscolhasServiceUnavailableException: Em 5xx, timeout ou resposta
            não-JSON.
        """
        url = f'{self.base_url}/api/v1/vagas-escolas/'
        params = {'processo_uuid': processo_uuid, 'cargo_codigo': str(cargo_codigo)}
        try:
            response = http_client.get(url, params=params, headers=self._default_headers, timeout=self.timeout_seconds)
        except RequestException as exc:
            logger.exception('Erro ao chamar API de escolha (vagas-escolas): %s', exc)
            raise EscolhasServiceUnavailableException(mensagem='Serviço de vagas por escola indisponível.', detalhes=str(exc)) from exc
        if response.status_code >= 500:
            logger.error('API escolha retornou status %s: %s', response.status_code, response.text[:500])
            raise EscolhasServiceUnavailableException(mensagem='Serviço de vagas por escola indisponível.', detalhes=f'Status {response.status_code}')
        if response.status_code != 200:
            raise EscolhasServiceUnavailableException(mensagem='Erro ao obter vagas por escola.', detalhes=f'Status {response.status_code}')
        try:
            data = response.json()
        except ValueError as exc:
            logger.exception('Resposta da API de escolha não é JSON válido.')
            raise EscolhasServiceUnavailableException(mensagem='Resposta inválida do serviço de vagas.', detalhes=str(exc)) from exc
        if not isinstance(data, dict):
            raise EscolhasServiceUnavailableException(mensagem='Resposta inválida do serviço de vagas.', detalhes='Esperado objeto JSON.')
        return data

    def get_escolhas(self, candidato_uuids: list[str], concurso_uuid: str) -> list[dict[str, Any]]:
        """POST {ESCOLHA_API_URL}/api/v1/escolhas/busca/.

        Body: {"candidato_uuid": [...], "concurso_uuid": "..."}.

        Retorna lista de Escolha com vaga_escola.escola.codigo_integracao.

        Raises:
            EscolhasServiceUnavailableException: em 5xx, timeout ou resposta
            inválida.
        """
        url = f'{self.base_url}/api/v1/escolhas/busca/'
        payload = {'candidato_uuid': [str(u) for u in candidato_uuids], 'concurso_uuid': str(concurso_uuid)}
        try:
            response = http_client.post(url, json=payload, headers=self._default_headers, timeout=self.timeout_seconds)
        except RequestException as exc:
            logger.exception('Erro ao chamar API de escolhas (busca lote): %s', exc)
            raise EscolhasServiceUnavailableException(mensagem='Serviço de escolhas indisponível.', detalhes=str(exc)) from exc
        if response.status_code >= 500:
            logger.error('API escolhas retornou status %s: %s', response.status_code, response.text[:500])
            raise EscolhasServiceUnavailableException(mensagem='Serviço de escolhas indisponível.', detalhes=f'Status {response.status_code}')
        if response.status_code != 200:
            raise EscolhasServiceUnavailableException(mensagem='Erro ao obter escolhas do lote.', detalhes=f'Status {response.status_code}')
        return response.json()  # type: ignore[no-any-return]

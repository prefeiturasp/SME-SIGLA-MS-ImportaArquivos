"""Serviços para integração com API externa."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from django.conf import settings
from requests.exceptions import RequestException

from ..models.log_request_http import LogRequestHttp
from ..serializers.importacao_escolhas import ResponseSerializer

logger = logging.getLogger(__name__)


class ApiProdamService:
    """Service para comunicação com a API PRODAM."""

    DEFAULT_TIMEOUT = 300

    def __init__(self, timeout_seconds: int = None) -> None:  # type: ignore[assignment]
        """Inicializa a instância com os parâmetros informados.

        Args:
            self: Instância do objeto.
            timeout_seconds: Tempo máximo de espera pela resposta, em segundos.

        Raises:
            ValueError: Se os dados informados forem inválidos.
        """
        self.timeout_seconds = timeout_seconds or self.DEFAULT_TIMEOUT
        self.api_url = settings.PRODAM_ESCOLHAS_API_URL
        self._token = settings.PRODAM_API_TOKEN
        self._usuario = settings.PRODAM_API_USUARIO
        self._senha = settings.PRODAM_API_SENHA
        if not self._token or not self._usuario or (not self._senha):
            raise ValueError(
                "Configurações da API externa não encontradas. Verifique PRODAM_API_TOKEN, PRODAM_API_USUARIO e PRODAM_API_SENHA no settings.py."
            )

    def _get_headers(self) -> dict[str, str]:
        """Obtém headers.

        Args:
            self: Instância do objeto.

        Returns:
            Dicionário com os dados retornados pela operação.
        """
        return {
            "Authorization": f"Basic {self._token}",
            "Content-Type": "application/json",
        }

    def consultar_resultado_convocacao_ingresso(
        self, processo_id: int
    ) -> dict[str, Any]:
        """Consulta resultado de convocação/ingresso na API PRODAM.

        Args:
            self: Instância do objeto.
            processo_id: Identificador de processo.

        Returns:
            Dicionário com os dados retornados pela operação.

        Raises:
            RequestException: Se a chamada HTTP falhar.
            ValueError: Se os dados informados forem inválidos.
        """
        url = self.api_url
        headers = self._get_headers()
        payload = {
            "usuario": self._usuario,
            "senha": self._senha,
            "identificadorChamadaSistema": processo_id,
        }
        response = None
        try:
            logger.info(f"Consultando API externa: processo_id={processo_id}")
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )  # type: ignore[arg-type]
            if response is not None:
                try:
                    LogRequestHttp.objects.create(
                        url=url,
                        metodo_http="POST",
                        processo_id=processo_id,
                        resposta_raw=response.text,
                    )  # type: ignore[misc]
                except Exception as log_exc:
                    logger.warning(f"Erro ao salvar log da chamada: {log_exc}")
            response.raise_for_status()
            data = json.loads(response.text)
            serializer = ResponseSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            logger.info(
                f'Resposta API externa recebida: retorno={data.get('retorno')}, registros={len(data.get('lstDadosResultadoConvocacaoIngresso', []))}'
            )
            return serializer.validated_data  # type: ignore[no-any-return]
        except RequestException as exc:
            logger.error(f"Erro ao consultar API externa: {exc}")
            raise RequestException(
                f"Erro ao consultar API externa: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(
                f"Erro inesperado ao processar resposta da API externa: {exc}"
            )
            raise ValueError(
                f"Erro ao processar resposta da API externa: {exc}"
            ) from exc

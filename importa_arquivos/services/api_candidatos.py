"""
Serviços para integração com API de candidatos.
"""
import logging
from typing import List, Dict, Any, Optional

import requests
from requests import RequestException
from importa_arquivos.services.erros import registrar_erro

logger = logging.getLogger(__name__)


class ApiCandidatosService:
    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _transformar_registros(self, registros: List[Dict[str, Any]], estrutura: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforma os registros do CSV para o formato esperado pela API.
        """
        mapa_coluna_para_payload: Dict[str, str] = {}
        for item in estrutura:
            if not isinstance(item, dict):
                continue
            coluna = item.get('coluna')
            campo_payload = item.get('campo_payload')
            if coluna and campo_payload:
                mapa_coluna_para_payload[str(coluna)] = str(campo_payload)

        transformados: List[Dict[str, Any]] = []
        for row in registros:
            novo: Dict[str, Any] = {}
            for coluna_original, valor in row.items():
                nome_payload = mapa_coluna_para_payload.get(coluna_original)
                if not nome_payload:
                    continue
                novo[nome_payload] = valor
            transformados.append(novo)
        return transformados

    def enviar_habilitados(
        self,
        registros: List[Dict[str, Any]],
        estrutura: List[Dict[str, Any]],
        concurso_uuid: str,
        concurso_nome: str,
        headers: Optional[Dict[str, str]] = None,
        importacao_obj: Optional[Any] = None,
    ) -> requests.Response:
        url = f"{self.base_url}/api/v1/candidatos"
        merged_headers = {**self._default_headers, **(headers or {})}

        dados_transformados = self._transformar_registros(registros, estrutura)

        payload = {
            'concurso_uuid': concurso_uuid,
            'concurso_nome': concurso_nome,
            'candidatos': dados_transformados,
        }
        try:
            response = requests.post(url, json=payload, headers=merged_headers, timeout=self.timeout_seconds)
            response.raise_for_status()
            logger.info('Candidatos enviados: %s (concurso=%s)', len(dados_transformados), concurso_uuid)
            return response
        except RequestException as exc:
            logger.error('Erro ao enviar candidatos: %s', exc)
            if importacao_obj is not None:
                try:
                    registrar_erro(importacao_obj, mensagem='Erro ao enviar candidatos para API externa', detalhes=str(exc), exc=exc)
                except Exception:
                    pass
            raise

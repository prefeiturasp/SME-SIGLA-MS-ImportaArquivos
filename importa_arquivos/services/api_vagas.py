import logging
from typing import List, Dict, Any, Optional

import requests
from datetime import datetime
from requests.exceptions import RequestException
from importa_arquivos.services.erros import registrar_erro

logger = logging.getLogger(__name__)


class ApiVagasService:
    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _transformar_registros(self, registros: List[Dict[str, Any]], estrutura: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforma os registros do CSV para o formato esperado pela API de vagas usando campo_payload do layout.
        """
        mapa: Dict[str, str] = {}
        for item in estrutura:
            if not isinstance(item, dict):
                continue
            coluna = item.get('coluna')
            campo_payload = item.get('campo_payload')
            if coluna and campo_payload:
                mapa[str(coluna)] = str(campo_payload)

        saida: List[Dict[str, Any]] = []
        for row in registros:
            novo: Dict[str, Any] = {}
            for coluna_original, valor in row.items():
                nome_payload = mapa.get(coluna_original)
                if not nome_payload:
                    continue
                if coluna_original == 'DATA' and isinstance(valor, str):
                    try:
                        valor = datetime.strptime(valor.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
                    except Exception:
                        pass
                novo[nome_payload] = valor
            saida.append(novo)
        return saida

    def enviar_vagas(self,
        registros: List[Dict[str, Any]],
        estrutura: List[Dict[str, Any]],
        processo_uuid: str = '',
        processo_nome: str = '',
        headers: Optional[Dict[str, str]] = None,
        importacao_obj: Optional[Any] = None,
    ) -> requests.Response:
        url = f"{self.base_url}/api/v1/vagas-escolas/"
        merged_headers = {**self._default_headers, **(headers or {})}
        dados = self._transformar_registros(registros, estrutura)
        payload = {
            'vagas': dados,
            'processo_uuid': processo_uuid,
            'processo_nome': processo_nome,
        }
        try:
            response = requests.post(url, json=payload, headers=merged_headers, timeout=self.timeout_seconds)
            response.raise_for_status()
            logger.info('Vagas enviadas: %s', len(dados))
            return response
        except RequestException as exc:
            logger.error('Erro ao enviar vagas: %s', exc)
            if importacao_obj is not None:
                try:
                    registrar_erro(importacao_obj, mensagem='Erro ao enviar vagas para API externa', detalhes=str(exc), exc=exc)
                except Exception:
                    pass
            raise
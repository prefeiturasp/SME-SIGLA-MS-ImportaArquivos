"""Módulo services/api_concursos."""
from __future__ import annotations
from typing import Any
import logging
import requests
from requests.exceptions import RequestException
from importa_arquivos.services.exceptions import CargoConcursoInvalidoException
logger = logging.getLogger(__name__)

class ApiConcursosService:
    """Define ApiConcursosService."""

    def __init__(self, base_url: str, timeout_seconds: int=10) -> None:
        """Executa   init  .
        
        Args:
            self: Instância do objeto.
            base_url: Parâmetro base url da operação.
            timeout_seconds: Parâmetro timeout seconds da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds

    def obter_codigos_cargo_do_concurso(self, concurso_uuid: str) -> set[int]:
        """Consulta GET {base_url}/api/v1/concursos/{concurso_uuid}/ e retorna.
        
        Args:
            self: Instância do objeto.
            concurso_uuid: Parâmetro concurso uuid da operação.
        
        Returns:
            Resultado da operação.
        
        Raises:
            CargoConcursoInvalidoException: se concurso não for encontrado.
        """
        url = f'{self.base_url}/api/v1/concursos/{concurso_uuid}/'
        try:
            response = requests.get(url, timeout=self.timeout_seconds)
        except RequestException as exc:
            logger.error('Erro ao consultar concursos API: %s', exc)
            raise CargoConcursoInvalidoException(mensagem='Serviço de concursos indisponível.', detalhes=str(exc)) from exc
        if response.status_code == 404:
            raise CargoConcursoInvalidoException(mensagem='Concurso não encontrado.', detalhes=f"Concurso UUID '{concurso_uuid}' não encontrado na API de concursos.")
        if response.status_code >= 500:
            raise CargoConcursoInvalidoException(mensagem='Serviço de concursos indisponível.', detalhes=f"Status {response.status_code} ao consultar concurso '{concurso_uuid}'.")
        cargos = response.json().get('cargos', [])
        return {int(cargo['codigo']) for cargo in cargos if cargo.get('codigo') is not None}

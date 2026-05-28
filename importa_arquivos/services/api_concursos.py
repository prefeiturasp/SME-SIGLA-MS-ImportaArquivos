import logging

import requests
from requests.exceptions import RequestException

from importa_arquivos.services.exceptions import CargoConcursoInvalidoException

logger = logging.getLogger(__name__)


class ApiConcursosService:
    def __init__(self, base_url: str, timeout_seconds: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def obter_codigos_cargo_do_concurso(self, concurso_uuid: str) -> set[int]:
        """
        Consulta GET {base_url}/api/v1/concursos/{concurso_uuid}/ e retorna
        o conjunto de códigos inteiros dos cargos vinculados ao concurso.

        Raises:
            CargoConcursoInvalidoException: se concurso não for encontrado
            (404),
                serviço indisponível (5xx) ou falha de conexão.
        """
        url = f"{self.base_url}/api/v1/concursos/{concurso_uuid}/"
        try:
            response = requests.get(url, timeout=self.timeout_seconds)
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

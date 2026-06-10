import contextlib
import logging
from datetime import datetime
from typing import Any

from requests.exceptions import RequestException
from sigla_sdk.http.api_client import http_client

from importa_arquivos.services.exceptions import (
    ApiEscolhasException,
    TipoUEDesabilitadoException,
)

from .erros import captura_erros_importacao

logger = logging.getLogger(__name__)


class ApiEscolhasService:
    def __init__(
        self, base_url: str = "https://example.com", timeout_seconds: int = 30
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Mantido compatível: método e contrato iguais ao antigo ApiVagasService  # noqa: E501

    def _transformar_registros(
        self, registros: list[dict[str, Any]], estrutura: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Transforma os registros do CSV para o formato esperado pela API usando
        campo_payload do layout.
        """
        mapa: dict[str, str] = {}
        for item in estrutura:
            if not isinstance(item, dict):
                continue
            coluna = item.get("coluna")
            campo_payload = item.get("campo_payload")
            if coluna and campo_payload:
                mapa[str(coluna)] = str(campo_payload)

        saida: list[dict[str, Any]] = []
        for row in registros:
            novo: dict[str, Any] = {}
            for coluna_original, valor in row.items():
                nome_payload = mapa.get(coluna_original)
                if not nome_payload:
                    continue
                if coluna_original == "DATA" and isinstance(valor, str):
                    with contextlib.suppress(Exception):
                        valor = datetime.strptime(
                            valor.strip(), "%d/%m/%Y"
                        ).strftime("%Y-%m-%d")
                novo[nome_payload] = valor
            saida.append(novo)
        return saida

    @captura_erros_importacao(param_nome_obj="importacao_obj")
    def enviar_vagas(
        self,
        registros: list[dict[str, Any]],
        estrutura: list[dict[str, Any]],
        processo_uuid: str = "",
        processo_nome: str = "",
        concurso_uuid: str = "",
        headers: dict[str, str] | None = None,
        importacao_obj: Any | None = None,
    ) -> dict:
        url = f"{self.base_url}/api/v1/vagas-escolas/"
        merged_headers = {**self._default_headers, **(headers or {})}
        dados = self._transformar_registros(registros, estrutura)
        payload = {
            "vagas": dados,
            "processo_uuid": processo_uuid,
            "processo_nome": processo_nome,
            "concurso_uuid": concurso_uuid,
        }
        try:
            response = http_client.post(
                url,
                json=payload,
                headers=merged_headers,
                timeout=self.timeout_seconds,
            )
            # Tratamento específico para erro de tipo_ue desabilitado
            if response.status_code == 400:
                try:
                    data = response.json()
                except Exception:
                    data = {}
                if (
                    isinstance(data, dict)
                    and data.get("code") == "TIPO_UE_DESABILITADO"
                ):
                    raise TipoUEDesabilitadoException(
                        mensagem=str(
                            data.get("detail") or "Tipo de UE desabilitado"
                        ),
                        detalhes="TIPO_UE_DESABILITADO",
                    )
            if response.status_code >= 400:
                raise ApiEscolhasException(
                    mensagem="Falha ao enviar vagas para API externa",
                    detalhes=response.text or f"Status {response.status_code}",
                    status_code=response.status_code,
                )
            logger.info("Vagas enviadas: %s", len(dados))
            return response.json()
        except RequestException as exc:
            logger.error("Erro ao enviar vagas: %s", exc)
            raise

    def _transformar_escolhas_prodam_para_escolhas(
        self, dados_prodam: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Transforma dados da Prodam para o formato esperado pelo MS-Escolhas.

        Args:
            dados_prodam: Lista de dicionários com dados da Prodam

        Returns:
            Lista de dicionários no formato esperado pelo MS-Escolhas
        """
        escolhas = []

        # Mapeamento de status da Prodam para situações do MS-Escolhas
        dados_prodam = [
            item
            for item in dados_prodam
            if item.get("descricaoStatus") == "ALOCADO"
        ]
        for item in dados_prodam:
            escolha = {
                "cpf": item.get("codigoPessoaFisica", ""),
                "codigo_cargo": item.get("codigoCargo", ""),
                "codigo_eol": item.get("codigoUnidadeAlocacao") or "",
                "tipo_vaga": item.get("tipoVaga") or "",
                "situacao": "ESCOLHA",
            }
            escolhas.append(escolha)

        return escolhas

    @captura_erros_importacao(param_nome_obj="importacao_obj")
    def enviar_escolhas_prodam(
        self,
        processo_uuid: str,
        concurso_uuid: str,
        dados_prodam: list[dict[str, Any]],
        headers: dict[str, str] | None = None,
        importacao_obj: Any | None = None,
    ) -> dict:
        """
        Envia escolhas da Prodam para o MS-Escolhas.

        Args:
            processo_uuid: UUID do processo de convocação
            concurso_uuid: UUID do concurso
            dados_prodam: Lista de dicionários com dados da Prodam
            headers: Headers adicionais para a requisição
            importacao_obj: Objeto de importação para registro de erros

        Returns:
            dict com resposta da requisição
        """
        url = f"{self.base_url}/api/v1/escolhas/importacao-prodam/"
        merged_headers = {**self._default_headers, **(headers or {})}

        # Transformar dados da Prodam para formato MS-Escolhas
        escolhas = self._transformar_escolhas_prodam_para_escolhas(
            dados_prodam
        )

        payload = {
            "processo_uuid": str(processo_uuid),
            "concurso_uuid": str(concurso_uuid),
            "escolhas": escolhas,
        }

        try:
            logger.info(
                f"Enviando {len(escolhas)} escolhas para MS-Escolhas (processo_uuid={processo_uuid})"  # noqa: E501
            )
            response = http_client.post(
                url,
                json=payload,
                headers=merged_headers,
                timeout=self.timeout_seconds,
            )
        except RequestException as exc:
            logger.error(f"Erro ao enviar escolhas para MS-Escolhas: {exc}")
            raise

        if response.status_code >= 400:
            raise ApiEscolhasException(
                mensagem="Falha ao enviar escolhas para API externa",
                detalhes=response.text or f"Status {response.status_code}",
                status_code=response.status_code,
            )

        logger.info(f"Escolhas enviadas com sucesso: {len(escolhas)}")
        return response.json()

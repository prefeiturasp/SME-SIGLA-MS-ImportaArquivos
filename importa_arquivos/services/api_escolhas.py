"""Módulo services/api_escolhas."""

from __future__ import annotations

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
    """Serviço para operações de apiescolhas."""

    def __init__(
        self, base_url: str = "https://example.com", timeout_seconds: int = 30
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            base_url: URL base do serviço remoto.
            timeout_seconds: Tempo máximo de espera pela resposta, em segundos.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _transformar_registros(
        self, registros: list[dict[str, Any]], estrutura: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Transforma os registros do CSV para o formato esperado pela API.

        Args:
            registros: Lista de registros lidos do arquivo ou da API.
            estrutura: Definição de colunas do layout de importação.

        Returns:
            Lista com os registros obtidos.
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
        headers: dict[str, str] | None = None,
        importacao_obj: Any | None = None,
    ) -> dict:
        """Envia vagas.

        Args:
            registros: Lista de registros lidos do arquivo ou da API.
            estrutura: Definição de colunas do layout de importação.
            processo_uuid: UUID do processo de convocação.
            processo_nome: Nome do processo exibido na resposta.
            headers: Cabeçalhos HTTP da requisição.
            importacao_obj: Registro de importação em andamento.

        Returns:
            Dicionário com os dados processados.

        Raises:
            ApiEscolhasException: Quando a API de escolhas falha ou retorna
                erro.
            TipoUEDesabilitadoException: Quando o tipo de UE informado está
                desabilitado para importação.
        """
        url = f"{self.base_url}/api/v1/vagas-escolas/"
        merged_headers = {**self._default_headers, **(headers or {})}
        dados = self._transformar_registros(registros, estrutura)
        payload = {
            "vagas": dados,
            "processo_uuid": processo_uuid,
            "processo_nome": processo_nome,
        }
        try:
            response = http_client.post(
                url,
                json=payload,
                headers=merged_headers,
                timeout=self.timeout_seconds,
            )
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
            return response.json()  # type: ignore[no-any-return]
        except RequestException as exc:
            logger.error("Erro ao enviar vagas: %s", exc)
            raise

    def _transformar_escolhas_prodam_para_escolhas(
        self, dados_prodam: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Converte payload Prodam para o formato do MS-Escolhas.

        Args:
            dados_prodam: Payload retornado pela API Prodam.

        Returns:
            Lista com os registros obtidos.
        """
        escolhas = []
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
        """Envia escolhas prodam.

        Args:
            processo_uuid: UUID do processo de convocação.
            concurso_uuid: UUID do concurso relacionado.
            dados_prodam: Payload retornado pela API Prodam.
            headers: Cabeçalhos HTTP da requisição.
            importacao_obj: Registro de importação em andamento.

        Returns:
            Dicionário com os dados processados.

        Raises:
            ApiEscolhasException: Quando a API de escolhas falha ou retorna
                erro.
        """
        url = f"{self.base_url}/api/v1/escolhas/importacao-prodam/"
        merged_headers = {**self._default_headers, **(headers or {})}
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
        return response.json()  # type: ignore[no-any-return]

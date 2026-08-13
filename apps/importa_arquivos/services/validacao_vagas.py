"""Módulo services/validacao_vagas."""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from importa_arquivos.repository import LayoutArquivoImportacaoRepository
from importa_arquivos.services.erros import captura_erros_importacao
from importa_arquivos.services.exceptions import (
    ColunaCSVInvalidaError,
    LayoutNaoConfiguradoError,
    LeituraCSVError,
)

logger = logging.getLogger(__name__)


@captura_erros_importacao(param_nome_obj="importacao_obj")
def validar_csv_vagas(
    arquivo: Any, importacao_obj: Any = None
) -> tuple[list[dict], list[dict]]:
    """O arquivo CSV deve conter as colunas: DataFechamentoModulo.

    Args:
        arquivo: Arquivo CSV a ser validado.
        importacao_obj: Importacao obj associado à validação.

    Returns:
        Tupla com os registros obtidos e a estrutura do layout.

    Raises:
        ColunaCSVInvalidaError: Se tiver colunas inválidas.
        LayoutNaoConfiguradoError: Se não tiver layout configurado.
        LeituraCSVError: Se não conseguir ler o arquivo CSV.
    """
    layout = LayoutArquivoImportacaoRepository.obter_mais_recente_por_tipo(
        "VAGAS"
    )
    if layout is None:
        raise LayoutNaoConfiguradoError("Layout VAGAS não configurado.")
    estrutura: list[dict] = layout["estrutura"] or []
    colunas_esperadas: set[str] = set()
    for item in estrutura:
        if not isinstance(item, dict):
            continue
        coluna = item.get("coluna")
        if isinstance(coluna, str):
            colunas_esperadas.add(coluna)
    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
    except Exception as exc:
        raise LeituraCSVError(
            "Erro ao ler arquivo CSV",
            detalhes=(
                "Não foi possível ler o arquivo CSV. " f"Detalhes: {exc!s}"
            ),
        ) from exc
    headers_csv = set(reader.fieldnames or [])
    if headers_csv != colunas_esperadas:
        logger.warning(f"Colunas inválidas no CSV: {headers_csv}")
        colunas_sobrando = headers_csv - colunas_esperadas
        mensagem_erro = "Colunas inválidas no arquivo CSV"
        detalhes_lista = []
        if colunas_sobrando:
            detalhes_lista.append(
                f"Colunas não esperadas: {sorted(colunas_sobrando)}"
            )
        detalhes_lista.append(
            f"Colunas esperadas para Vagas: {sorted(colunas_esperadas)}"
        )
        detalhes_lista.append(f"Encontradas: {sorted(headers_csv)}")
        detalhes = " | ".join(detalhes_lista)
        raise ColunaCSVInvalidaError(mensagem_erro, detalhes=detalhes)
    registros: list[dict] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        registros.append(row)
    return (registros, estrutura)

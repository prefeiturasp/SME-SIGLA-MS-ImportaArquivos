"""Módulo services/validacao_vagas."""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from importa_arquivos.models import LayoutArquivoImportacao
from importa_arquivos.services.exceptions import (
    ColunaCSVInvalidaException,
    LayoutNaoConfiguradoException,
    LeituraCSVException,
)

from .erros import captura_erros_importacao

logger = logging.getLogger(__name__)


@captura_erros_importacao(param_nome_obj="importacao_obj")
def validar_csv_vagas(
    arquivo: Any, importacao_obj: Any = None
) -> tuple[list[dict], list[dict]]:
    """Valida csv vagas.

    Args:
        arquivo: Arquivo utilizado na operação.
        importacao_obj: Importacao obj utilizado na operação.

    Returns:
        Tupla com os objetos criados ou atualizados.

    Raises:
        ColunaCSVInvalidaException: Se ocorrer erro nesta operação.
        LayoutNaoConfiguradoException: Se ocorrer erro nesta operação.
        LeituraCSVException: Se ocorrer erro nesta operação.
    """
    try:
        layout = LayoutArquivoImportacao.objects.filter(tipo="VAGAS").latest(
            "criado_em"
        )
    except LayoutArquivoImportacao.DoesNotExist:
        raise LayoutNaoConfiguradoException(
            "Layout VAGAS não configurado."
        ) from None
    estrutura: list[dict] = layout.estrutura or []
    colunas_esperadas = {
        item.get("coluna") for item in estrutura if isinstance(item, dict)
    }
    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
    except Exception as exc:
        raise LeituraCSVException(
            "Erro ao ler arquivo CSV",
            detalhes=(
                "Não foi possível ler o arquivo CSV. " f"Detalhes: {exc!s}"
            ),
        ) from exc
    headers_csv = set(reader.fieldnames or [])
    if headers_csv != colunas_esperadas:
        logger.warning(f"Colunas inválidas no CSV: {headers_csv}")
        colunas_esperadas - headers_csv
        colunas_sobrando = headers_csv - colunas_esperadas
        mensagem_erro = "Colunas inválidas no arquivo CSV"
        detalhes_lista = []
        if colunas_sobrando:
            detalhes_lista.append(
                f"Colunas não esperadas: {sorted(colunas_sobrando)}"
            )
        detalhes_lista.append(
            f"Colunas esperadas para Vagas: {sorted(colunas_esperadas)}"
        )  # type: ignore[type-var]
        detalhes_lista.append(f"Encontradas: {sorted(headers_csv)}")
        detalhes = " | ".join(detalhes_lista)
        raise ColunaCSVInvalidaException(mensagem_erro, detalhes=detalhes)
    registros: list[dict] = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        registros.append(row)
    return (registros, estrutura)

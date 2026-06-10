"""Serviço de validação e processamento de arquivos de lote (SIGPEC).

O arquivo é um TXT delimitado por ';' com header fixo:
LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC

Nota: CHAVE_INSCRITO é ignorada — equivale ao codigo_inscricao já existente no
candidato.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from pydantic import ValidationError

from importa_arquivos.services.erros import captura_erros_importacao
from importa_arquivos.services.exceptions import (
    ArquivoLotesVazioException,
    ColunaCSVInvalidaException,
    ErrosValidacaoLotesException,
    LeituraCSVException,
)
from importa_arquivos.services.schema import COLUNAS_ESPERADAS, LinhaLoteSIGPEC

logger = logging.getLogger(__name__)


def _validar_linha_lote(
    row: dict, num_linha: int, lote_referencia: int | None
) -> tuple[LinhaLoteSIGPEC | None, str, int | None]:
    """Valida uma linha do arquivo de lotes via schema Pydantic.

    Args:
        row: Row utilizado na operação.
        num_linha: Num linha utilizado na operação.
        lote_referencia: Lote referencia utilizado na operação.

    Returns:
        Tupla com os objetos criados ou atualizados.
    """
    identificacao = row.get("IDENTIFICACAO", "").strip()
    try:
        obj = LinhaLoteSIGPEC(
            lote=row.get("LOTE", "").strip(),
            empresa=row.get("EMPRESA", "").strip(),
            vaga=row.get("VAGA", "").strip(),
            identificacao=row.get("IDENTIFICACAO", "").strip(),
            chave_inscrito=row.get("CHAVE_INSCRITO", "").strip(),
            numfunc=row.get("NUMFUNC", "").strip(),
            numvinc=row.get("NUMVINC", "").strip() or None,
        )
    except ValidationError as exc:
        erros = "\n".join(
            [
                f"Linha: {num_linha} | Identificacao: {identificacao} - Campo '{e['loc'][0]}': {e['msg']}"  # noqa: E501
                for e in exc.errors()
            ]
        )
        return (None, erros, lote_referencia)
    if lote_referencia is None:
        lote_referencia = obj.lote
    elif obj.lote != lote_referencia:
        return (
            None,
            f"Linha: {num_linha} | Identificacao: {identificacao} - Lote {obj.lote} diverge do lote inicial {lote_referencia}.",  # noqa: E501
            lote_referencia,
        )
    return (obj, "", lote_referencia)


@captura_erros_importacao(param_nome_obj="importacao_obj")
def validar_txt_lotes(
    arquivo: Any, importacao_obj: Any = None
) -> list[dict[str, Any]]:
    """Valida txt lotes.

    Args:
        arquivo: Arquivo utilizado na operação.
        importacao_obj: Importacao obj utilizado na operação.

    Returns:
        Lista com os registros obtidos.

    Raises:
        ArquivoLotesVazioException: Se ocorrer erro nesta operação.
        ColunaCSVInvalidaException: Se ocorrer erro nesta operação.
        ErrosValidacaoLotesException: Se ocorrer erro nesta operação.
        LeituraCSVException: Se ocorrer erro nesta operação.
    """
    try:
        file_bytes = arquivo.read()
        arquivo.seek(0)
        text = file_bytes.decode("utf-8-sig")
    except Exception as exc:
        raise LeituraCSVException(
            mensagem="Nao foi possivel ler o arquivo de lotes.",
            detalhes=f"Detalhes tecnicos: {exc}",
        ) from exc
    if not text or not text.strip():
        raise ArquivoLotesVazioException(
            mensagem="O arquivo de lotes esta vazio.",
            detalhes="Arquivo sem conteudo util para processamento.",
        )
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    headers_csv = {h for h in reader.fieldnames or [] if h}
    colunas_faltando = COLUNAS_ESPERADAS - headers_csv
    if colunas_faltando:
        raise ColunaCSVInvalidaException(
            mensagem="Cabecalho invalido para importacao de lotes.",
            detalhes=f"Colunas ausentes: {sorted(colunas_faltando)}. Esperado: {sorted(COLUNAS_ESPERADAS)}",  # noqa: E501
        )
    registros: list[dict[str, Any]] = []
    erros: list[str] = []
    lote_referencia: int | None = None
    for row in reader:
        valores = [
            v for k, v in row.items() if k and v is not None and str(v).strip()
        ]
        if not valores:
            continue
        obj, erro, lote_referencia = _validar_linha_lote(
            row, reader.line_num, lote_referencia
        )
        if erro:
            erros.append(erro)
        else:
            registros.append(obj.model_dump())  # type: ignore[union-attr]
    if not registros:
        raise ArquivoLotesVazioException(
            mensagem="O arquivo nao contem registros validos.",
            detalhes="Apenas cabecalho ou linhas vazias foram encontradas.",
        )
    if erros:
        raise ErrosValidacaoLotesException(
            mensagem="Erro ao validar os dados do arquivo.",
            detalhes="\n".join(erros),
        )
    logger.info("validar_txt_lotes: %d registros validos.", len(registros))
    return registros

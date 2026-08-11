"""Módulo services/erros."""

from __future__ import annotations

import contextlib
import traceback
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.db import transaction

from importa_arquivos.models import ImportacaoErro
from importa_arquivos.services.exceptions import BaseImportacaoException


def _repositorio_para_instancia(importacao_obj: Any) -> Any:
    """Retorna a classe de repository responsável por atualizar o status.

    Args:
        importacao_obj: Registro de importação em andamento.

    Returns:
        Classe de repository correspondente ao tipo de importacao_obj.
    """
    from importa_arquivos.models import (
        ImportacaoArquivoHabilitado,
        ImportacaoArquivoVagas,
        ImportacaoEscolhas,
        ImportacaoLotes,
    )
    from importa_arquivos.repository import (
        ImportacaoArquivoHabilitadoRepository,
        ImportacaoArquivoVagasRepository,
        ImportacaoEscolhasRepository,
        ImportacaoLotesRepository,
    )

    repositorio_por_modelo = {
        ImportacaoArquivoHabilitado: ImportacaoArquivoHabilitadoRepository,
        ImportacaoArquivoVagas: ImportacaoArquivoVagasRepository,
        ImportacaoLotes: ImportacaoLotesRepository,
        ImportacaoEscolhas: ImportacaoEscolhasRepository,
    }
    return repositorio_por_modelo[type(importacao_obj)]


def registrar_erro(
    importacao_obj: Any,
    mensagem: str | None = None,
    detalhes: str | None = None,
    exc: Exception | None = None,
) -> ImportacaoErro:
    """Registrar erro.

    Args:
        importacao_obj: Registro de importação em andamento.
        mensagem: Mensagem principal do erro.
        detalhes: Detalhes complementares do erro.
        exc: Exceção capturada durante o processamento.

    Returns:
        Registro de erro criado no banco.

    Raises:
        ValueError: Se os dados informados forem inválidos.
    """
    from importa_arquivos.repository import ImportacaoErroRepository

    if importacao_obj is None:
        raise ValueError("importacao_obj é obrigatório para registrar erro")
    if exc is not None:
        if isinstance(exc, BaseImportacaoException):
            mensagem = mensagem or exc.mensagem
            detalhes = detalhes or exc.detalhes
        else:
            mensagem = mensagem or exc.__class__.__name__
            detalhes = detalhes or traceback.format_exc()
    if not mensagem:
        mensagem = "Erro durante importação"
    if detalhes is None:
        detalhes = ""
    _repositorio_para_instancia(importacao_obj).atualizar_status(
        importacao_obj, "ERRO"
    )
    with transaction.atomic():
        return ImportacaoErroRepository.criar(
            importacao_obj=importacao_obj,
            mensagem=mensagem,
            erros=detalhes,
        )


def captura_erros_importacao(
    param_nome_obj: str = "importacao_obj",
) -> Callable:
    """Decorator para funções de serviço de importação.

    Args:
        param_nome_obj: Nome do parâmetro que recebe o objeto de importação.

    Returns:
        Decorador que registra falhas e relança a exceção original.
    """

    def decorator(func: Callable) -> Callable:
        """Decorator para registrar erros de importação."""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper para capturar erros de importação."""
            importacao_obj = kwargs.get(param_nome_obj)
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if importacao_obj is not None:
                    with contextlib.suppress(Exception):
                        registrar_erro(importacao_obj, exc=exc)
                raise

        return wrapper

    return decorator

from typing import Callable, Optional, Any
from functools import wraps
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from importa_arquivos.models import ImportacaoErro
from importa_arquivos.services.exceptions import BaseImportacaoException
import traceback


def registrar_erro(importacao_obj: Any, mensagem: Optional[str] = None, detalhes: Optional[str] = None, exc: Exception | None = None) -> ImportacaoErro:
    if importacao_obj is None:
        raise ValueError('importacao_obj é obrigatório para registrar erro')

    if exc is not None:
        if isinstance(exc, BaseImportacaoException):
            mensagem = mensagem or exc.mensagem
            detalhes = detalhes or exc.detalhes
        else:
            mensagem = mensagem or exc.__class__.__name__
            detalhes = detalhes or traceback.format_exc()

    if not mensagem:
        mensagem = 'Erro durante importação'
    if detalhes is None:
        detalhes = ''

    content_type = ContentType.objects.get_for_model(importacao_obj.__class__)
    importacao_obj.status = 'ERRO'
    importacao_obj.save(update_fields=['status'])
    with transaction.atomic():
        return ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=getattr(importacao_obj, 'uuid', getattr(importacao_obj, 'id')),
            mensagem=mensagem,
            erros=detalhes,
        )


def captura_erros_importacao(param_nome_obj: str = 'importacao_obj') -> Callable:
    """
    Decorator para funções de serviço de importação.
    Se ocorrer exceção, registra em ImportacaoErro usando o parâmetro indicado e relança.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            importacao_obj = kwargs.get(param_nome_obj)
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if importacao_obj is not None:
                    try:
                        registrar_erro(importacao_obj, exc=exc)
                    except Exception:
                        pass
                raise
        return wrapper
    return decorator 
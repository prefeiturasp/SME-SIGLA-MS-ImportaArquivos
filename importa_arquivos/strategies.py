"""
Strategies para tratamento de responses do robust server.
"""
from abc import ABC, abstractmethod
from typing import Protocol
from rest_framework import status
from .constants import ImportacaoStatus


class ImportacaoUpdater(Protocol):
    """Protocol para objetos que podem ter status atualizado."""
    
    def update_status(self, new_status: ImportacaoStatus) -> None:
        """Atualiza o status da importação."""
        ...


class ResponseHandler(ABC):
    """Strategy abstrata para tratamento de responses."""
    
    @abstractmethod
    def can_handle(self, status_code: int) -> bool:
        """Verifica se pode tratar este status code."""
        pass
    
    @abstractmethod
    def handle(self, importacao: ImportacaoUpdater) -> None:
        """Trata o response atualizando a importação."""
        pass


class SuccessResponseHandler(ResponseHandler):
    """Handler para responses de sucesso (200, 201)."""
    
    def can_handle(self, status_code: int) -> bool:
        return status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
    
    def handle(self, importacao: ImportacaoUpdater) -> None:
        importacao.update_status(ImportacaoStatus.PROCESSANDO)


class ClientErrorResponseHandler(ResponseHandler):
    """Handler para erros do cliente (400, 409, 422)."""
    
    def can_handle(self, status_code: int) -> bool:
        return status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    def handle(self, importacao: ImportacaoUpdater) -> None:
        importacao.update_status(ImportacaoStatus.ERRO)


class ServerErrorResponseHandler(ResponseHandler):
    """Handler para erros do servidor (500+)."""
    
    def can_handle(self, status_code: int) -> bool:
        return status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def handle(self, importacao: ImportacaoUpdater) -> None:
        importacao.update_status(ImportacaoStatus.ERRO)


class UnknownResponseHandler(ResponseHandler):
    """Handler para status codes não reconhecidos."""
    
    def can_handle(self, status_code: int) -> bool:
        return True  # Fallback para qualquer status não tratado
    
    def handle(self, importacao: ImportacaoUpdater) -> None:
        importacao.update_status(ImportacaoStatus.ERRO)


class ResponseHandlerChain:
    """Chain of Responsibility para handlers de response."""
    
    def __init__(self):
        self._handlers = [
            SuccessResponseHandler(),
            ClientErrorResponseHandler(),
            ServerErrorResponseHandler(),
            UnknownResponseHandler(),  # Deve ser o último (fallback)
        ]
    
    def handle_response(self, status_code: int, importacao: ImportacaoUpdater) -> None:
        """Processa o response usando o handler apropriado."""
        for handler in self._handlers:
            if handler.can_handle(status_code):
                handler.handle(importacao)
                break


class ExceptionHandler:
    """Handler para exceções durante integração."""
    
    @staticmethod
    def handle_connection_error(importacao: ImportacaoUpdater) -> None:
        """Trata erro de conexão."""
        importacao.update_status(ImportacaoStatus.ERRO)
    
    @staticmethod
    def handle_timeout_error(importacao: ImportacaoUpdater) -> None:
        """Trata erro de timeout."""
        importacao.update_status(ImportacaoStatus.ERRO)
    
    @staticmethod
    def handle_generic_error(importacao: ImportacaoUpdater) -> None:
        """Trata erro genérico."""
        importacao.update_status(ImportacaoStatus.ERRO)

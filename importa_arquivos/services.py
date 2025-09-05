"""
Services para integração e processamento de arquivos.
"""
import base64
import os
from datetime import datetime
from typing import Dict, Any, Optional
import requests
import requests.exceptions
from django.conf import settings

from .constants import RobustServerConstants, ImportacaoStatus
from .strategies import ResponseHandlerChain, ExceptionHandler, ImportacaoUpdater


class PayloadBuilder:
    """Builder para construção de payloads de integração."""
    
    def __init__(self):
        self._payload: Dict[str, Any] = {}
    
    def with_uuid(self, uuid: str) -> 'PayloadBuilder':
        """Adiciona UUID ao payload."""
        self._payload['uuid'] = str(uuid)
        return self
    
    def with_basic_info(self, nome: str, descricao: Optional[str], 
                       tipo_layout: str, status: str) -> 'PayloadBuilder':
        """Adiciona informações básicas ao payload."""
        self._payload.update({
            'nome': nome,
            'descricao': descricao,
            'tipo_de_layout': tipo_layout,
            'status': status
        })
        return self
    
    def with_file_info(self, nome_arquivo: str, content_base64: str, 
                      content_type: str) -> 'PayloadBuilder':
        """Adiciona informações do arquivo ao payload."""
        self._payload['arquivo'] = {
            'name': nome_arquivo,
            'content': content_base64,
            'content_type': content_type
        }
        return self
    
    def with_metadata(self, criado_em: datetime) -> 'PayloadBuilder':
        """Adiciona metadata ao payload."""
        self._payload['metadata'] = {
            'criado_em': criado_em.isoformat(),
            'fonte': RobustServerConstants.FONTE_SISTEMA
        }
        return self
    
    def build(self) -> Dict[str, Any]:
        """Constrói e retorna o payload final."""
        return self._payload.copy()


class FileEncoder:
    """Responsável por codificação de arquivos."""
    
    @staticmethod
    def encode_to_base64(file_content: bytes) -> str:
        """Codifica conteúdo do arquivo para base64."""
        return base64.b64encode(file_content).decode('utf-8')


class RobustServerClient:
    """Cliente para comunicação com robust server."""
    
    def __init__(self):
        self._base_url = getattr(settings, 'ROBUST_SERVER_URL', 'http://localhost:8003')
        self._endpoint = f"{self._base_url}{RobustServerConstants.ENDPOINT_PATH}"
        self._headers = {
            'Content-Type': 'application/json',
            'User-Agent': RobustServerConstants.USER_AGENT
        }
    
    def send_file(self, payload: Dict[str, Any]) -> requests.Response:
        """Envia arquivo para o robust server."""
        return requests.post(
            self._endpoint,
            json=payload,
            headers=self._headers,
            timeout=RobustServerConstants.TIMEOUT_SECONDS
        )


class RobustServerIntegrationService:
    """Service para integração com robust server."""
    
    def __init__(self):
        self._client = RobustServerClient()
        self._response_handler = ResponseHandlerChain()
        self._exception_handler = ExceptionHandler()
    
    def send_validated_file(self, importacao: ImportacaoUpdater, 
                          file_content: bytes) -> None:
        """
        Envia arquivo validado para o robust server.
        
        Args:
            importacao: Objeto que implementa ImportacaoUpdater
            file_content: Conteúdo do arquivo em bytes
        """
        try:
            payload = self._build_payload(importacao, file_content)
            response = self._client.send_file(payload)
            self._handle_response(response.status_code, importacao)
            
        except requests.exceptions.ConnectionError:
            self._exception_handler.handle_connection_error(importacao)
        except requests.exceptions.Timeout:
            self._exception_handler.handle_timeout_error(importacao)
        except Exception:
            self._exception_handler.handle_generic_error(importacao)
    
    def _build_payload(self, importacao: ImportacaoUpdater, 
                      file_content: bytes) -> Dict[str, Any]:
        """Constrói payload para envio."""
        encoded_content = FileEncoder.encode_to_base64(file_content)
        
        return (PayloadBuilder()
                .with_uuid(importacao.uuid)
                .with_basic_info(
                    importacao.nome,
                    importacao.descricao,
                    importacao.tipo_de_layout,
                    importacao.status
                )
                .with_file_info(
                    importacao.arquivo_nome_original,
                    encoded_content,
                    importacao.arquivo_content_type
                )
                .with_metadata(importacao.criado_em)
                .build())
    
    def _handle_response(self, status_code: int, importacao: ImportacaoUpdater) -> None:
        """Processa response do robust server."""
        self._response_handler.handle_response(status_code, importacao)


class FileValidationService:
    """Service para validação de arquivos CSV."""
    
    def __init__(self):
        from .validators import CSVLayoutValidator  # Import local para evitar circular
        self._validator = CSVLayoutValidator()
    
    def validate_file_against_layout(self, file_content: bytes, 
                                   layout_type: str) -> None:
        """
        Valida arquivo contra layout específico.
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            layout_type: Tipo do layout para validação
            
        Raises:
            ValidationError: Se validação falhar
        """
        self._validator.validate(file_content, layout_type)
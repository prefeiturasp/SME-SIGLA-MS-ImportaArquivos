"""
Constantes e enums para o módulo de importação de arquivos.
"""
from enum import Enum
from typing import List, Dict, Any


class ImportacaoStatus(Enum):
    """Enum para status de importação."""
    PENDENTE = 'pendente'
    PROCESSANDO = 'processando'
    CONCLUIDO = 'concluido'
    ERRO = 'erro'

    @classmethod
    def choices(cls) -> List[tuple]:
        """Retorna choices para usar em Django models."""
        return [(status.value, status.value.title()) for status in cls]


class TipoLayout(Enum):
    """Enum para tipos de layout."""
    VAGAS = 'VAGAS'
    CANDIDATOS_CLASSIFICADOS = 'CANDIDATOS_CLASSIFICADOS'

    @classmethod
    def choices(cls) -> List[tuple]:
        """Retorna choices para usar em Django models."""
        return [
            (cls.VAGAS.value, 'Vagas'),
            (cls.CANDIDATOS_CLASSIFICADOS.value, 'Candidatos Classificados'),
        ]


class FileValidationConstants:
    """Constantes para validação de arquivos."""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_ENCODINGS = ['utf-8-sig', 'utf-8', 'latin-1']
    CSV_CONTENT_TYPE = 'text/csv'
    DEFAULT_FILENAME = 'arquivo.csv'


class RobustServerConstants:
    """Constantes para integração com robust server."""
    TIMEOUT_SECONDS = 30
    USER_AGENT = 'SME-SIGLA-ImportaArquivos/1.0'
    ENDPOINT_PATH = '/api/importacao-arquivos/'
    FONTE_SISTEMA = 'SME-SIGLA-MS-ImportaArquivos'


class ValidationMessages:
    """Mensagens de validação padronizadas."""
    
    @staticmethod
    def arquivo_vazio() -> str:
        return "Arquivo CSV vazio ou sem cabeçalhos."
    
    @staticmethod
    def campos_faltando(layout: str, campos: List[str], esperados: List[str]) -> str:
        return (
            f"O arquivo não corresponde ao layout {layout}. "
            f"Campos obrigatórios faltando: {', '.join(campos)}. "
            f"Campos esperados: {', '.join(esperados)}"
        )
    
    @staticmethod
    def campos_extras(layout: str, campos: List[str], permitidos: List[str]) -> str:
        return (
            f"O arquivo contém campos não esperados para o layout {layout}: "
            f"{', '.join(campos)}. "
            f"Campos permitidos: {', '.join(permitidos)}"
        )
    
    @staticmethod
    def layout_nao_encontrado(layout: str) -> str:
        return f"Layout não encontrado para o tipo: {layout}"
    
    @staticmethod
    def encoding_erro() -> str:
        return "Arquivo deve estar em formato UTF-8."
    
    @staticmethod
    def csv_erro(error: str) -> str:
        return f"Erro ao processar arquivo CSV: {error}"
    
    @staticmethod
    def validacao_erro(error: str) -> str:
        return f"Erro ao validar arquivo: {error}"

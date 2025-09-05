"""
Validators para arquivos CSV e layouts.
"""
import csv
import io
from typing import List
from django.core.exceptions import ValidationError

from .constants import FileValidationConstants, ValidationMessages


class CSVReader:
    """Responsável por leitura de arquivos CSV."""
    
    @staticmethod
    def read_headers(file_content: bytes) -> List[str]:
        """
        Lê os headers de um arquivo CSV.
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            
        Returns:
            Lista com os headers do arquivo
            
        Raises:
            ValidationError: Se não conseguir ler o arquivo
        """
        try:
            # Tentar diferentes encodings
            for encoding in FileValidationConstants.ALLOWED_ENCODINGS:
                try:
                    text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValidationError(ValidationMessages.encoding_erro())
            
            # Ler primeira linha (cabeçalhos)
            reader = csv.reader(io.StringIO(text))
            headers = next(reader, [])
            
            if not headers:
                raise ValidationError(ValidationMessages.arquivo_vazio())
            
            # Limpar headers (remover BOM e espaços)
            return [header.strip().lstrip('\ufeff') for header in headers]
            
        except csv.Error as e:
            raise ValidationError(ValidationMessages.csv_erro(str(e)))
        except Exception as e:
            raise ValidationError(ValidationMessages.validacao_erro(str(e)))


class LayoutProvider:
    """Provedor de layouts para validação."""
    
    @staticmethod
    def get_expected_fields(layout_type: str) -> List[str]:
        """
        Obtém campos esperados para um tipo de layout.
        
        Args:
            layout_type: Tipo do layout
            
        Returns:
            Lista com campos esperados
            
        Raises:
            ValidationError: Se layout não for encontrado
        """
        try:
            from .models import Layout  # Import local para evitar circular
            layout = Layout.objects.get(tipo_de_layout=layout_type)
            return [campo['campo'] for campo in layout.get_campos_ordenados()]
        except Layout.DoesNotExist:
            raise ValidationError(ValidationMessages.layout_nao_encontrado(layout_type))


class FieldValidator:
    """Validator para campos de um layout."""
    
    @staticmethod
    def validate_required_fields(headers: List[str], expected_fields: List[str], 
                                layout_type: str) -> None:
        """
        Valida se todos os campos obrigatórios estão presentes.
        
        Args:
            headers: Headers encontrados no arquivo
            expected_fields: Campos esperados do layout
            layout_type: Tipo do layout
            
        Raises:
            ValidationError: Se campos obrigatórios estiverem faltando
        """
        missing_fields = [field for field in expected_fields if field not in headers]
        
        if missing_fields:
            raise ValidationError(
                ValidationMessages.campos_faltando(layout_type, missing_fields, expected_fields)
            )
    
    @staticmethod
    def validate_no_extra_fields(headers: List[str], expected_fields: List[str], 
                                layout_type: str) -> None:
        """
        Valida se não há campos extras no arquivo.
        
        Args:
            headers: Headers encontrados no arquivo
            expected_fields: Campos esperados do layout
            layout_type: Tipo do layout
            
        Raises:
            ValidationError: Se houver campos extras
        """
        extra_fields = [header for header in headers if header not in expected_fields]
        
        if extra_fields:
            raise ValidationError(
                ValidationMessages.campos_extras(layout_type, extra_fields, expected_fields)
            )


class CSVLayoutValidator:
    """Validator principal para arquivos CSV contra layouts."""
    
    def __init__(self):
        self._csv_reader = CSVReader()
        self._layout_provider = LayoutProvider()
        self._field_validator = FieldValidator()
    
    def validate(self, file_content: bytes, layout_type: str) -> None:
        """
        Valida arquivo CSV contra layout específico.
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            layout_type: Tipo do layout para validação
            
        Raises:
            ValidationError: Se validação falhar
        """
        # Ler headers do arquivo
        headers = self._csv_reader.read_headers(file_content)
        
        # Obter campos esperados do layout
        expected_fields = self._layout_provider.get_expected_fields(layout_type)
        
        # Validar campos
        self._field_validator.validate_required_fields(headers, expected_fields, layout_type)
        self._field_validator.validate_no_extra_fields(headers, expected_fields, layout_type)

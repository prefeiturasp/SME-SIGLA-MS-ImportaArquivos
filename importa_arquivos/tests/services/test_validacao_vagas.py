"""Módulo tests/services/test_validacao_vagas."""
from __future__ import annotations
from typing import Any
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from importa_arquivos.services.exceptions import ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException
from importa_arquivos.services.validacao_vagas import validar_csv_vagas
pytestmark = pytest.mark.django_db

def test_validar_csv_vagas_sucesso(layout_vagas: Any) -> None:
    """Verifica validar csv vagas sucesso.
    
    Args:
        layout_vagas: Parâmetro layout vagas da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    csv = 'DataFechamentoModulo\n05/09/2025\n'
    arquivo = SimpleUploadedFile('v.csv', csv.encode('utf-8'), content_type='text/csv')
    registros, estrutura = validar_csv_vagas(arquivo)
    assert len(registros) == 1
    assert registros[0]['DataFechamentoModulo'] == '05/09/2025'
    assert isinstance(estrutura, list)

def test_validar_csv_vagas_sem_layout() -> None:
    """Verifica validar csv vagas sem layout.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')
    with pytest.raises(LayoutNaoConfiguradoException):
        validar_csv_vagas(arquivo)

def test_validar_csv_vagas_erro_leitura_utf8(layout_vagas: Any) -> None:
    """Verifica validar csv vagas erro leitura utf8.
    
    Args:
        layout_vagas: Parâmetro layout vagas da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    conteudo_invalido = b'\xff\xfe\xfa\xfb'
    arquivo = SimpleUploadedFile('v.csv', conteudo_invalido, content_type='text/csv')
    with pytest.raises(LeituraCSVException) as excinfo:
        validar_csv_vagas(arquivo)
    assert str(excinfo.value) == 'Erro ao ler arquivo CSV'
    assert hasattr(excinfo.value, 'detalhes')

def test_validar_csv_vagas_colunas_invalidas(layout_vagas: Any) -> None:
    """Verifica validar csv vagas colunas invalidas.
    
    Args:
        layout_vagas: Parâmetro layout vagas da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    csv = 'OutroHeader\nvalor\n'
    arquivo = SimpleUploadedFile('v.csv', csv.encode('utf-8'), content_type='text/csv')
    with pytest.raises(ColunaCSVInvalidaException) as excinfo:
        validar_csv_vagas(arquivo)
    assert str(excinfo.value) == 'Colunas inválidas no arquivo CSV'
    assert hasattr(excinfo.value, 'detalhes')

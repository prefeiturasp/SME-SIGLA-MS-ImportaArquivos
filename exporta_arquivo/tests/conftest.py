"""Módulo tests/conftest."""
from __future__ import annotations
from typing import Any
import pytest
from rest_framework.test import APIClient
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client() -> Any:
    """Cliente API para testes (DRF APIClient).
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return APIClient()

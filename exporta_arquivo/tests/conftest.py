import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """Cliente API para testes (DRF APIClient)."""
    return APIClient()

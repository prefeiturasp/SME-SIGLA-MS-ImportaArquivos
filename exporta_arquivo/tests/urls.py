"""URLconf mínimo para testes do exporta_arquivo (evita carregar.

e outras apps).
"""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("exporta_arquivo.urls")),
]

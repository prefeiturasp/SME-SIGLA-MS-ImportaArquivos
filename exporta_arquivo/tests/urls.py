"""URLconf mínimo para testes do exporta_arquivo (evita carregar importa_arquivos e outras apps)."""
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('exporta_arquivo.urls')),
]

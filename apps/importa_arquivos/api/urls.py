"""Módulo api/urls."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ImportacaoArquivoHabilitadosViewSet,
    ImportacaoArquivoVagasViewSet,
    ImportacaoEscolhasViewSet,
    ImportacaoLotesViewSet,
    LayoutArquivoImportacaoViewSet,
)

router = DefaultRouter()
router.register(
    r"importacao-arquivo/habilitados",
    ImportacaoArquivoHabilitadosViewSet,
    basename="importacao-arquivo-habilitados",
)
router.register(
    r"importacao-arquivo/vagas",
    ImportacaoArquivoVagasViewSet,
    basename="importacao-arquivo-vagas",
)
router.register(
    r"importacao-escolhas",
    ImportacaoEscolhasViewSet,
    basename="importacao-escolhas",
)
router.register(
    r"layouts", LayoutArquivoImportacaoViewSet, basename="layout-arquivo"
)
router.register(
    r"importacao/lotes", ImportacaoLotesViewSet, basename="importacao-lotes"
)

urlpatterns = [
    path("", include(router.urls)),
]

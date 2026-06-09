"""Módulo urls."""

from rest_framework.routers import DefaultRouter

from .views import (
    CabecalhoExportacaoLoteViewSet,
    ExportacaoCandidatosProcessoViewSet,
    ExportacaoLoteViewSet,
    ExportacaoVagasProcessoViewSet,
    ExportacaoVagasSigpecViewSet,
)

router = DefaultRouter()
router.register(
    r"exportacao/vagas-sigpec",
    ExportacaoVagasSigpecViewSet,
    basename="exportacao-vagas-sigpec",
)
router.register(
    r"exportacao/vagas-processo",
    ExportacaoVagasProcessoViewSet,
    basename="exportacao-vagas-processo",
)
router.register(
    r"exportacao/candidatos-processo",
    ExportacaoCandidatosProcessoViewSet,
    basename="exportacao-candidatos-processo",
)
router.register(
    r"exportacao/lote",
    ExportacaoLoteViewSet,
    basename="exportacao-lote",
)
router.register(
    r"exportacao/cabecalho-lote",
    CabecalhoExportacaoLoteViewSet,
    basename="cabecalho-exportacao-lote",
)

urlpatterns = router.urls

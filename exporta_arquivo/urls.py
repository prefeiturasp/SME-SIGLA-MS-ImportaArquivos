from rest_framework.routers import DefaultRouter
from .views import (
    ExportacaoVagasSigpecViewSet,
    ExportacaoVagasProcessoViewSet,
    ExportacaoCandidatosProcessoViewSet,
)

router = DefaultRouter()
router.register(
    r'exportacao/vagas-sigpec',
    ExportacaoVagasSigpecViewSet,
    basename='exportacao-vagas-sigpec',
)
router.register(
    r'exportacao/vagas-processo',
    ExportacaoVagasProcessoViewSet,
    basename='exportacao-vagas-processo',
)
router.register(
    r'exportacao/candidatos-processo',
    ExportacaoCandidatosProcessoViewSet,
    basename='exportacao-candidatos-processo',
)

urlpatterns = router.urls

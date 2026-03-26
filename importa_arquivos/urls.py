from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.importacao_habilitados import ImportacaoArquivoHabilitadosViewSet
from .views.layout import LayoutArquivoImportacaoViewSet
from .views.importacao_vagas import ImportacaoArquivoVagasViewSet
from .views.importacao_escolhas import ImportacaoEscolhasViewSet
from .views.importacao_lotes import ImportacaoLotesViewSet


router = DefaultRouter()
router.register(r'importacao-arquivo/habilitados', ImportacaoArquivoHabilitadosViewSet, basename='importacao-arquivo-habilitados')
router.register(r'importacao-arquivo/vagas', ImportacaoArquivoVagasViewSet, basename='importacao-arquivo-vagas')
router.register(r'importacao-escolhas', ImportacaoEscolhasViewSet, basename='importacao-escolhas')
router.register(r'layouts', LayoutArquivoImportacaoViewSet, basename='layout-arquivo')
router.register(r'importacao/lotes', ImportacaoLotesViewSet, basename='importacao-lotes')

urlpatterns = [
    path('', include('exporta_arquivo.urls')),
    path('', include(router.urls)),
] 
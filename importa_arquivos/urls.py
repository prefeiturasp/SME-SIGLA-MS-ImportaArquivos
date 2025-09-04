"""
URL configuration for the importa_arquivos module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImportacaoArquivosViewSet, LayoutViewSet

router = DefaultRouter()
router.register(r'importacao-arquivos', ImportacaoArquivosViewSet, basename='importacao-arquivo')
router.register(r'layouts', LayoutViewSet, basename='layout')

urlpatterns = [
    path('', include(router.urls)),
] 
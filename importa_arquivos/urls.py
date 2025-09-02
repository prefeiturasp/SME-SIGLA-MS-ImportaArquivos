"""
URL configuration for the importa_arquivos module.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImportacaoArquivosViewSet

router = DefaultRouter()
router.register(r'importacao-arquivos', ImportacaoArquivosViewSet, basename='importacao-arquivo')

urlpatterns = [
    path('', include(router.urls)),
] 
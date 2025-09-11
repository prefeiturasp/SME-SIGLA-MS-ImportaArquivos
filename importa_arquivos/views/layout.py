from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter

from ..models.layout import LayoutArquivoImportacao
from ..serializers.layout import LayoutArquivoImportacaoSerializer


class LayoutArquivoImportacaoViewSet(viewsets.ModelViewSet):
    queryset = LayoutArquivoImportacao.objects.all()
    serializer_class = LayoutArquivoImportacaoSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo']
    search_fields = ['tipo']
    ordering_fields = ['tipo', 'criado_em']
    ordering = ['-criado_em']

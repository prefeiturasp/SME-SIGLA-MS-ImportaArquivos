from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .models import ImportacaoArquivos, Layout
from .serializers import (
    ImportacaoArquivosSerializer, 
    ImportacaoArquivosListSerializer,
    ImportacaoArquivosSelectSerializer,
    LayoutSerializer,
    LayoutListSerializer,
    LayoutSelectSerializer
)
from .utils import CustomPagination


class ImportacaoArquivosViewSet(viewsets.ModelViewSet):
    queryset = ImportacaoArquivos.objects.all()
    serializer_class = ImportacaoArquivosSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nome', 'status']
    search_fields = ['nome', 'descricao']
    ordering_fields = ['nome', 'status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.query_params.get('formato') == 'select':
                return ImportacaoArquivosSelectSerializer
            return ImportacaoArquivosListSerializer
        return ImportacaoArquivosSerializer


class LayoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar layouts de importação.
    """
    queryset = Layout.objects.all()
    serializer_class = LayoutSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo_de_layout']
    search_fields = ['tipo_de_layout']
    ordering_fields = ['tipo_de_layout', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.query_params.get('formato') == 'select':
                return LayoutSelectSerializer
            return LayoutListSerializer
        return LayoutSerializer

    @action(detail=True, methods=['get'])
    def campos_ordenados(self, request, pk=None):
        """
        Retorna os campos do layout ordenados pela ordem.
        """
        layout = self.get_object()
        campos = layout.get_campos_ordenados()
        return Response({
            'uuid': layout.uuid,
            'tipo_de_layout': layout.tipo_de_layout,
            'total_campos': layout.total_campos,
            'campos': campos
        })

    @action(detail=False, methods=['get'])
    def tipos_disponiveis(self, request):
        """
        Retorna os tipos de layout disponíveis.
        """
        tipos = [{'value': choice[0], 'label': choice[1]} for choice in Layout.TIPO_LAYOUT_CHOICES]
        return Response(tipos)
 
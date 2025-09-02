from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .models import ImportacaoArquivos
from .serializers import (
    ImportacaoArquivosSerializer, 
    ImportacaoArquivosListSerializer,
    ImportacaoArquivosSelectSerializer
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
 
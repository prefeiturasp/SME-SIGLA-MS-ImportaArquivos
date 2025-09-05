from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
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
    filterset_fields = ['nome', 'tipo_de_layout', 'status']
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
    
    def create(self, request, *args, **kwargs):
        """
        Criar nova importação com tratamento de erros e status codes apropriados.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, 
                    status=status.HTTP_201_CREATED, 
                    headers=headers
                )
            else:
                return Response(
                    serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValidationError as e:
            return Response(
                {"validation_errors": e.messages if hasattr(e, 'messages') else [str(e)]}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """
        Atualizar importação com status codes apropriados.
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    serializer.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ImportacaoArquivos.DoesNotExist:
            return Response(
                {"error": "Importação não encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {"validation_errors": e.messages if hasattr(e, 'messages') else [str(e)]}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Deletar importação com status codes apropriados.
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ImportacaoArquivos.DoesNotExist:
            return Response(
                {"error": "Importação não encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
        try:
            layout = self.get_object()
            campos = layout.get_campos_ordenados()
            return Response({
                'uuid': layout.uuid,
                'tipo_de_layout': layout.tipo_de_layout,
                'total_campos': layout.total_campos,
                'campos': campos
            }, status=status.HTTP_200_OK)
        except Layout.DoesNotExist:
            return Response(
                {"error": "Layout não encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def tipos_disponiveis(self, request):
        """
        Retorna os tipos de layout disponíveis.
        """
        try:
            tipos = [{'value': choice[0], 'label': choice[1]} for choice in Layout.TIPO_LAYOUT_CHOICES]
            return Response(tipos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
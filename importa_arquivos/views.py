from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from .models import ImportacaoArquivos
from .layout_service import LayoutService
from .serializers import (
    ImportacaoArquivosSerializer, 
    ImportacaoArquivosListSerializer,
    ImportacaoArquivosSelectSerializer,
    LayoutSerializer,
    LayoutCreateSerializer,
    LayoutListSerializer,
    LayoutSelectSerializer
)
from .utils import CustomPagination


class ImportacaoArquivosViewSet(viewsets.ModelViewSet):
    queryset = ImportacaoArquivos.objects.all()
    serializer_class = ImportacaoArquivosSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['concurso', 'cargo', 'tipo_de_layout', 'status']
    search_fields = ['concurso', 'cargo']
    ordering_fields = ['concurso', 'cargo', 'status', 'criado_em']
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
        from .services import RobustServerCommunicationError
        
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
        except RobustServerCommunicationError as e:
            # Erro de comunicação com robust server - retornar 503 Service Unavailable
            return Response(
                {
                    'error': 'Serviço temporariamente indisponível',
                    'message': e.message,
                    'error_type': e.error_type,
                    'details': 'O servidor de processamento não está acessível. Tente novamente mais tarde.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
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
        except (ImportacaoArquivos.DoesNotExist, Http404):
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
        except (ImportacaoArquivos.DoesNotExist, Http404):
            return Response(
                {"error": "Importação não encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LayoutViewSet(viewsets.ViewSet):
    """
    ViewSet para gerenciar layouts de importação armazenados em JSON.
    """
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.query_params.get('formato') == 'select':
                return LayoutSelectSerializer
            return LayoutListSerializer
        return LayoutSerializer
    
    def list(self, request):
        """
        Lista todos os layouts.
        """
        try:
            layouts = LayoutService.list_layouts()
            
            # Aplicar filtros
            tipo_filter = request.query_params.get('tipo_de_layout')
            if tipo_filter:
                layouts = [l for l in layouts if l.get('tipo_de_layout') == tipo_filter]
            
            # Aplicar busca
            search = request.query_params.get('search')
            if search:
                layouts = [l for l in layouts if search.lower() in l.get('tipo_de_layout', '').lower()]
            
            # Ordenação
            ordering = request.query_params.get('ordering', '-criado_em')
            reverse_order = ordering.startswith('-')
            order_field = ordering.lstrip('-')
            
            if order_field == 'criado_em':
                layouts = sorted(layouts, key=lambda x: x.get('criado_em', ''), reverse=reverse_order)
            elif order_field == 'tipo_de_layout':
                layouts = sorted(layouts, key=lambda x: x.get('tipo_de_layout', ''), reverse=reverse_order)
            
            serializer_class = self.get_serializer_class()
            serializer = serializer_class(layouts, many=True)
            
            return Response({
                'count': len(layouts),
                'results': serializer.data
            })
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Erro interno: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        """
        Busca um layout específico por UUID.
        """
        try:
            layout = LayoutService.get_layout_by_uuid(pk)
            if not layout:
                return Response({'error': 'Layout não encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = LayoutSerializer(layout)
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Erro interno: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request):
        """
        Cria um novo layout.
        Aceita apenas tipo_de_layout e dados no payload.
        """
        try:
            # Usar LayoutCreateSerializer para validar apenas os campos necessários
            create_serializer = LayoutCreateSerializer(data=request.data)
            if create_serializer.is_valid():
                layout = LayoutService.create_layout(create_serializer.validated_data)
                # Usar LayoutSerializer para retornar todos os campos
                response_serializer = LayoutSerializer(layout)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Erro interno: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, pk=None):
        """
        Atualiza um layout existente.
        Aceita apenas tipo_de_layout e dados no payload.
        """
        try:
            layout = LayoutService.get_layout_by_uuid(pk)
            if not layout:
                return Response({'error': 'Layout não encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            # Usar LayoutCreateSerializer para validar apenas os campos necessários
            create_serializer = LayoutCreateSerializer(data=request.data)
            if create_serializer.is_valid():
                updated_layout = LayoutService.update_layout(pk, create_serializer.validated_data)
                # Usar LayoutSerializer para retornar todos os campos
                response_serializer = LayoutSerializer(updated_layout)
                return Response(response_serializer.data)
            else:
                return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Erro interno: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request, pk=None):
        """
        Atualização parcial de um layout.
        """
        return self.update(request, pk)
    
    def destroy(self, request, pk=None):
        """
        Remove um layout.
        """
        try:
            if LayoutService.delete_layout(pk):
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Layout não encontrado'}, status=status.HTTP_404_NOT_FOUND)
                
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Erro interno: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def campos_ordenados(self, request, pk=None):
        """
        Retorna os campos do layout ordenados pela ordem.
        """
        try:
            layout = LayoutService.get_layout_by_uuid(pk)
            if not layout:
                return Response(
                    {"error": "Layout não encontrado"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            dados = layout.get('dados', [])
            campos_ordenados = sorted(dados, key=lambda x: x.get('ordem', 0))
            
            return Response({
                'uuid': layout.get('uuid'),
                'tipo_de_layout': layout.get('tipo_de_layout'),
                'total_campos': len(dados),
                'campos': campos_ordenados
            }, status=status.HTTP_200_OK)
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
            tipos_disponiveis = LayoutService.get_tipos_layout_disponiveis()
            tipos = [{'value': tipo, 'label': tipo} for tipo in tipos_disponiveis]
            return Response(tipos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 
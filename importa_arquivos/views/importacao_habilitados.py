from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from ..services.validacao_habilitados import validar_csv_habilitados
from ..services.api_candidatos import ApiCandidatosService
from ..models import ImportacaoArquivoHabilitado
from ..serializers import (
    ImportacaoArquivoHabilitadosCreateSerializer, 
    ImportacaoArquivoHabilitadosListSerializer,
)
from ..utils import CustomPagination


class ImportacaoArquivoHabilitadosViewSet(viewsets.ModelViewSet):
    queryset = ImportacaoArquivoHabilitado.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nome_arquivo', 'status', 'concurso_uuid', 'concurso_nome']
    search_fields = ['concurso_uuid', 'concurso_nome']
    ordering_fields = ['nome_arquivo', 'status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ImportacaoArquivoHabilitadosListSerializer
        return ImportacaoArquivoHabilitadosCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        arquivo = serializer.validated_data.get('arquivo')

        concurso_uuid = serializer.validated_data.get('concurso_uuid') or request.data.get('concurso_uuid')
        concurso_nome = serializer.validated_data.get('concurso_nome') or request.data.get('concurso_nome')

        try:
            registros, estrutura = validar_csv_habilitados(arquivo)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logging.error('Erro inesperado na validação do CSV: %s', exc)
            return Response({'detail': 'Erro ao validar CSV.'}, status=status.HTTP_400_BAD_REQUEST)

        response = super().create(request, *args, **kwargs)

        try:
            ApiCandidatosService(
                base_url=settings.CANDIDATOS_API_URL,
            ).enviar_habilitados(
                registros=registros,
                estrutura=estrutura,
                concurso_uuid=str(concurso_uuid) if concurso_uuid else '',
                concurso_nome=str(concurso_nome) if concurso_nome else '',
            )
        except Exception as exc:
            logging.error('Falha ao enviar dados para API externa: %s', exc)

        return response

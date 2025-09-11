from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from django.conf import settings

from ..models import ImportacaoArquivoVagas
from ..serializers import (
    ImportacaoArquivoVagasCreateSerializer,
    ImportacaoArquivoVagasListSerializer,
)
from ..services.validacao_vagas import validar_csv_vagas
from ..services.api_vagas import ApiVagasService
from ..utils import CustomPagination


class ImportacaoArquivoVagasViewSet(viewsets.ModelViewSet):
    queryset = ImportacaoArquivoVagas.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nome_arquivo', 'status']
    search_fields = ['nome_arquivo']
    ordering_fields = ['nome_arquivo', 'status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ImportacaoArquivoVagasListSerializer
        return ImportacaoArquivoVagasCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        arquivo = serializer.validated_data.get('arquivo')

        try:
            registros, estrutura = validar_csv_vagas(arquivo)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logging.error('Erro inesperado na validação do CSV (VAGAS): %s', exc)
            return Response({'detail': 'Erro ao validar CSV.'}, status=status.HTTP_400_BAD_REQUEST)

        response = super().create(request, *args, **kwargs)

        try:
            ApiVagasService(base_url=settings.ESCOLHAS_API_URL).enviar_vagas(
                registros=registros,
                estrutura=estrutura,
            )
        except Exception as exc:
            logging.error('Falha ao enviar vagas para API externa: %s', exc)

        return response

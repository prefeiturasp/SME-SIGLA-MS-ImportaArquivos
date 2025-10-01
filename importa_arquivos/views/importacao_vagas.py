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
    filterset_fields = ['nome_arquivo', 'status', 'processo_uuid', 'processo_nome']
    search_fields = ['processo_uuid', 'processo_nome']
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
        instance = serializer.save()

        processo_uuid = serializer.validated_data.get('processo_uuid') or request.data.get('processo_uuid')
        processo_nome = serializer.validated_data.get('processo_nome') or request.data.get('processo_nome')

        try:
            registros, estrutura = validar_csv_vagas(instance.arquivo, importacao_obj=instance)
        except Exception as exc:
            logging.error('Erro inesperado na validação do CSV: %s', exc)
            return Response({'detail': 'Erro ao validar CSV.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ApiVagasService(
                base_url=settings.ESCOLHA_API_URL,
            ).enviar_vagas(
                registros=registros,
                estrutura=estrutura,
                processo_uuid=str(instance.processo_uuid) if instance.processo_uuid else '',
                processo_nome=str(instance.processo_nome) if instance.processo_nome else '',
                importacao_obj=instance,
            )
        except Exception as exc:
            logging.error('Falha ao enviar dados para API externa: %s', exc)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
    filterset_fields = ['nome_arquivo', 'status', 'concurso_uuid', 'concurso_nome']
    search_fields = ['concurso_uuid', 'concurso_nome']
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

        concurso_uuid = serializer.validated_data.get('concurso_uuid') or request.data.get('concurso_uuid')
        concurso_nome = serializer.validated_data.get('concurso_nome') or request.data.get('concurso_nome')

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
                concurso_uuid=str(instance.concurso_uuid) if instance.concurso_uuid else '',
                concurso_nome=str(instance.concurso_nome) if instance.concurso_nome else '',
                importacao_obj=instance,
            )
        except Exception as exc:
            logging.error('Falha ao enviar dados para API externa: %s', exc)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

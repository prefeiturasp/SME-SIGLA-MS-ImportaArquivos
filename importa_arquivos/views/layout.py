from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
import csv
import io
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from ..models.base import CHOICES_TIPO_IMPORTACAO_ARQUIVO

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

    @extend_schema(
        description='Faz o download de um arquivo CSV contendo apenas o cabeçalho definido no layout do tipo informado.',
        parameters=[
            OpenApiParameter(
                name='tipo',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Tipo de layout',
                enum=[opcao[0] for opcao in CHOICES_TIPO_IMPORTACAO_ARQUIVO],
            )
        ],
        responses={200: 'text/csv'}
    )
    @action(detail=False, methods=['get'], url_path='download')
    def download(self, request):
        tipo = request.query_params.get('tipo')
        if not tipo:
            return Response({'detail': 'Parâmetro tipo é obrigatório.'}, status=400)

        layout = LayoutArquivoImportacao.objects.filter(tipo=tipo).first()
        if not layout:
            return Response({'detail': 'Layout não encontrado para o tipo informado.'}, status=404)

        estrutura = layout.estrutura or []
        colunas = [str(item.get('coluna')) for item in estrutura if isinstance(item, dict) and item.get('coluna')]

        delimiter = ';' if str(tipo).upper() == 'VAGAS' else ','

        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=delimiter)
        if colunas:
            writer.writerow(colunas)
        content = buffer.getvalue()

        response = HttpResponse(content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="layout_{str(tipo).lower()}.csv"'
        return response

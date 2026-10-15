"""ViewSet de layout de arquivos de importação."""

from __future__ import annotations

import csv
import io
from typing import Any

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from importa_arquivos.api.schemas.layout import OPERACOES_LAYOUTS, TAG_LAYOUTS
from importa_arquivos.models.layout import LayoutArquivoImportacao
from importa_arquivos.repository import LayoutArquivoImportacaoRepository
from importa_arquivos.serializers.layout import (
    LayoutArquivoImportacaoSerializer,
)


@extend_schema(tags=[TAG_LAYOUTS])
@extend_schema_view(**OPERACOES_LAYOUTS)
class LayoutArquivoImportacaoViewSet(viewsets.ModelViewSet):
    """ViewSet para o recurso LayoutArquivoImportacao."""

    queryset = LayoutArquivoImportacao.objects.all()
    serializer_class = LayoutArquivoImportacaoSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["tipo"]
    search_fields = ["tipo"]
    ordering_fields = ["tipo", "criado_em"]
    ordering = ["-criado_em"]

    @action(detail=False, methods=["get"], url_path="download")
    def download(self, request: Any) -> Any:
        """Download do layout de importação de arquivos em formato CSV."""
        tipo = request.query_params.get("tipo")
        if not tipo:
            return Response(
                {"detail": "Parâmetro tipo é obrigatório."}, status=400
            )
        layout = LayoutArquivoImportacaoRepository.obter_por_tipo(tipo)
        if not layout:
            return Response(
                {"detail": "Layout não encontrado para o tipo informado."},
                status=404,
            )
        estrutura = layout["estrutura"] or []
        colunas = [
            str(item.get("coluna"))
            for item in estrutura
            if isinstance(item, dict) and item.get("coluna")
        ]
        delimiter = ";" if str(tipo).upper() == "VAGAS" else ","
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=delimiter)
        if colunas:
            writer.writerow(colunas)
        content = buffer.getvalue()
        response = HttpResponse(
            content, content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="layout_{str(tipo).lower()}.csv"'
        )
        return response

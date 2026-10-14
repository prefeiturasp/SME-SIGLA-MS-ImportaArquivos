"""ViewSet do cabeçalho configurável de exportação de lotes."""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny

from ...models import CabecalhoExportacaoLote
from ...serializers import CabecalhoExportacaoLoteSerializer
from ..schemas.cabecalho_exportacao_lote import (
    OPERACOES_CABECALHO_EXPORTACAO_LOTE,
    TAG_CABECALHO_EXPORTACAO_LOTE,
)


@extend_schema(tags=[TAG_CABECALHO_EXPORTACAO_LOTE])
@extend_schema_view(**OPERACOES_CABECALHO_EXPORTACAO_LOTE)
class CabecalhoExportacaoLoteViewSet(viewsets.ModelViewSet):
    """CRUD para o cabeçalho configurável de exportação de lotes."""

    queryset = CabecalhoExportacaoLote.objects.all()
    serializer_class = CabecalhoExportacaoLoteSerializer
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["ativo"]
    ordering = ["-criado_em"]

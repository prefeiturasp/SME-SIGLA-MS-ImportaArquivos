"""ViewSet de exportação de lotes (SIGPEC/ERGON)."""

from __future__ import annotations

import logging
from typing import Any

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from exporta_arquivo.api.views.base import _sanitizar_nome_arquivo
from exporta_arquivo.models import ExportacaoLote
from exporta_arquivo.models.exportacao_lote import StatusExportacao
from exporta_arquivo.repository import ExportacaoLoteRepository
from exporta_arquivo.serializers import (
    ExportacaoLoteCreateSerializer,
    ExportacaoLoteListSerializer,
)
from exporta_arquivo.services.exceptions import (
    BaseExportacaoError,
    ExportacaoLoteIncompletaError,
)
from exporta_arquivo.services.exportacao_lote import exportar_lote
from importa_arquivos.utils import CustomPagination

logger = logging.getLogger(__name__)


class ExportacaoLoteViewSet(viewsets.ModelViewSet):
    """ViewSet para exportação de lotes.

    - POST /exportacao/lote/  → exporta lote; retorna arquivo .txt (200) ou
      arquivo de erro (422)
    - GET  /exportacao/lote/  → lista histórico paginado
    - GET  /exportacao/lote/<uuid>/         → detalhe
    - GET  /exportacao/lote/<uuid>/download/ → redownload do arquivo
    """

    queryset = ExportacaoLote.objects.all()
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "concurso_uuid",
        "lote_uuid",
        "concurso_nome",
        "numero_lote",
        "codigo_cargo",
    ]
    search_fields = ["concurso_nome"]
    ordering_fields = ["criado_em", "atualizado_em"]
    ordering = ["-criado_em"]
    pagination_class = CustomPagination

    def get_serializer_class(self) -> Any:
        """Retorna serializer class de acordo com a action."""
        if self.action in ("list", "retrieve"):
            return ExportacaoLoteListSerializer
        return ExportacaoLoteCreateSerializer

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Cria o registro de exportação."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        try:
            conteudo = exportar_lote(instance)
        except ExportacaoLoteIncompletaError as exc:
            logger.warning(
                "Exportação incompleta (422) para o lote %s: %s",
                instance.uuid,
                exc.mensagem,
            )
            nomes = exc.candidatos_sem_escolha
            conteudo_erro = self._gerar_conteudo_erro(nomes, instance)
            lote_id = (
                instance.numero_lote
                if instance.numero_lote is not None
                else str(instance.lote_uuid)
            )
            nome_arquivo_erro = f"candidatos_sem_escolha_lote_{_sanitizar_nome_arquivo(str(lote_id))}.txt"  # noqa: E501
            ExportacaoLoteRepository.atualizar(
                instance,
                conteudo_arquivo=conteudo_erro,
                nome_arquivo=nome_arquivo_erro,
                status=StatusExportacao.ATENCAO,
            )
            response = HttpResponse(
                conteudo_erro.encode("utf-8"),
                content_type="text/plain; charset=utf-8",
                status=422,
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{nome_arquivo_erro}"'
            )
            return response
        except BaseExportacaoError as exc:
            logger.warning(
                f"Exportação: {instance.uuid} | {exc.mensagem} | {exc.detalhes}"  # noqa: E501
            )
            ExportacaoLoteRepository.atualizar(
                instance, status=StatusExportacao.ERRO
            )
            return Response(
                {"mensagem": exc.mensagem, "detail": exc.detalhes},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lote_id = (
            instance.numero_lote
            if instance.numero_lote is not None
            else str(instance.lote_uuid)
        )
        nome_arquivo = (
            f"exportacao_lote_{_sanitizar_nome_arquivo(str(lote_id))}.txt"
        )
        ExportacaoLoteRepository.atualizar(
            instance,
            conteudo_arquivo=conteudo,
            nome_arquivo=nome_arquivo,
            status=StatusExportacao.SUCESSO,
        )
        response = HttpResponse(
            conteudo.encode("utf-8"), content_type="text/plain; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{nome_arquivo}"'
        )
        return response

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request: Any, uuid: Any = None) -> Any:
        """Redownload do arquivo exportado (sucesso ou erro).

        Args:
            request: Requisição HTTP recebida.
            uuid: Identificador único do registro.

        Returns:
            Valor convertido ou validado.
        """
        instance = self.get_object()
        if not instance.conteudo_arquivo:
            return Response(
                {"detail": "Arquivo não disponível para este registro."},
                status=status.HTTP_404_NOT_FOUND,
            )
        response = HttpResponse(
            instance.conteudo_arquivo.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{instance.nome_arquivo}"'
        )
        return response

    @staticmethod
    def _gerar_conteudo_erro(nomes: list, instance: ExportacaoLote) -> str:
        """Gera conteudo erro.

        Args:
            nomes: Nomes dos candidatos sem escolha realizada.
            instance: Instância do modelo em atualização.

        Returns:
            Texto com os nomes dos candidatos sem escolha realizada.
        """
        lote_id = (
            instance.numero_lote
            if instance.numero_lote is not None
            else instance.lote_uuid
        )
        linhas = [f"Candidatos sem escolha realizada no lote {lote_id}:"]
        for nome in nomes:
            linhas.append(f"- {nome}")
        return "\n".join(linhas) + "\n"

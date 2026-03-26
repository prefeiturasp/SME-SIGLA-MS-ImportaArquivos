"""
Views para exportação de lotes e gerenciamento do cabeçalho.

ExportacaoLoteViewSet:
  - POST /exportacao/lote/  → exporta lote; retorna arquivo .txt (200) ou arquivo de erro (422)
  - GET  /exportacao/lote/  → lista histórico paginado
  - GET  /exportacao/lote/<uuid>/         → detalhe
  - GET  /exportacao/lote/<uuid>/download/ → redownload do arquivo

CabecalhoExportacaoLoteViewSet:
  - CRUD completo para edição do cabeçalho configurável
"""
import re

from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from importa_arquivos.utils import CustomPagination

from ..models import ExportacaoLote, CabecalhoExportacaoLote
from ..serializers import (
    ExportacaoLoteCreateSerializer,
    ExportacaoLoteListSerializer,
    CabecalhoExportacaoLoteSerializer,
)
from ..services.exportacao_lote import exportar_lote, ExportacaoLoteIncompletaException
from ..services.exceptions import (
    ExportacaoBadRequestException,
    ExportacaoNotFoundException,
    ExportacaoServiceUnavailableException,
)


def _sanitizar_nome_arquivo(texto: str, max_len: int = 80) -> str:
    if not texto or not isinstance(texto, str):
        return "arquivo"
    s = re.sub(r"[^\w\s\-]", "", texto, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s.strip())
    return (s[:max_len] if len(s) > max_len else s) or "arquivo"


class ExportacaoLoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para exportação de lotes.

    - create: valida, executa exportação e retorna arquivo .txt (200) ou
              arquivo de erro com nomes de candidatos sem escolha (422).
    - list: histórico paginado de exportações.
    - retrieve: detalhe de uma exportação.
    - download (GET /<uuid>/download/): redownload do arquivo exportado.
    """
    queryset = ExportacaoLote.objects.all()
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["concurso_uuid", "lote_uuid", "concurso_nome"]
    search_fields = ["concurso_nome"]
    ordering_fields = ["criado_em", "atualizado_em"]
    ordering = ["-criado_em"]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ExportacaoLoteListSerializer
        return ExportacaoLoteCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        try:
            conteudo = exportar_lote(instance)
        except ExportacaoLoteIncompletaException as exc:
            # Candidatos sem escolha: retorna arquivo de erro com HTTP 422
            nomes = exc.candidatos_sem_escolha
            conteudo_erro = self._gerar_conteudo_erro(nomes, instance)
            nome_arquivo_erro = f"candidatos_sem_escolha_lote_{_sanitizar_nome_arquivo(str(instance.lote_uuid))}.txt"

            # Persiste o arquivo de erro no histórico
            instance.conteudo_arquivo = conteudo_erro
            instance.nome_arquivo = nome_arquivo_erro
            instance.save(update_fields=["conteudo_arquivo", "nome_arquivo"])

            response = HttpResponse(
                conteudo_erro.encode("utf-8"),
                content_type="text/plain; charset=utf-8",
                status=422,
            )
            response["Content-Disposition"] = f'attachment; filename="{nome_arquivo_erro}"'
            return response

        except ExportacaoBadRequestException as exc:
            return Response({"detail": exc.mensagem}, status=status.HTTP_400_BAD_REQUEST)
        except ExportacaoNotFoundException as exc:
            return Response({"detail": exc.mensagem}, status=status.HTTP_404_NOT_FOUND)
        except ExportacaoServiceUnavailableException as exc:
            return Response({"detail": exc.mensagem}, status=status.HTTP_502_BAD_GATEWAY)

        nome_arquivo = (
            f"exportacao_lote_{_sanitizar_nome_arquivo(str(instance.lote_uuid))}.txt"
        )
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.save(update_fields=["conteudo_arquivo", "nome_arquivo"])

        response = HttpResponse(
            conteudo.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
        return response

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, uuid=None):
        """Redownload do arquivo exportado (sucesso ou erro)."""
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
        response["Content-Disposition"] = f'attachment; filename="{instance.nome_arquivo}"'
        return response

    @staticmethod
    def _gerar_conteudo_erro(nomes: list, instance: ExportacaoLote) -> str:
        linhas = [
            f"Candidatos sem escolha realizada no lote {instance.lote_uuid}:",
        ]
        for nome in nomes:
            linhas.append(f"- {nome}")
        return "\n".join(linhas) + "\n"


class CabecalhoExportacaoLoteViewSet(viewsets.ModelViewSet):
    """
    CRUD para o cabeçalho configurável de exportação de lotes.
    Use GET / para listar, POST para criar, PATCH/<uuid>/ para editar.
    """
    queryset = CabecalhoExportacaoLote.objects.all()
    serializer_class = CabecalhoExportacaoLoteSerializer
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["ativo"]
    ordering = ["-criado_em"]

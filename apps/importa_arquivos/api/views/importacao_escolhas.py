"""ViewSet de importação de escolhas."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from requests.exceptions import RequestException
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from importa_arquivos.models import ImportacaoEscolhas
from importa_arquivos.models.constants import MODO_IMPORTACAO_MANUAL
from importa_arquivos.repository import ImportacaoErroRepository
from importa_arquivos.serializers import (
    ImportacaoEscolhasCreateSerializer,
    ImportacaoEscolhasListSerializer,
)
from importa_arquivos.services.exceptions import (
    ApiEscolhasError,
    ApiProdamError,
)
from importa_arquivos.services.importacao_escolhas_service import (
    ImportacaoEscolhasService,
)
from importa_arquivos.utils import CustomPagination

logger = logging.getLogger(__name__)


class ImportacaoEscolhasViewSet(viewsets.ModelViewSet):
    """ViewSet para o recurso ImportacaoEscolhas."""

    queryset = ImportacaoEscolhas.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["processo_uuid", "status", "processo_id", "modo"]
    search_fields = ["processo_uuid"]
    ordering_fields = ["status", "criado_em"]
    ordering = ["-criado_em"]
    pagination_class = CustomPagination
    lookup_field = "uuid"

    def get_serializer_class(self) -> Any:
        """Retorna serializer class.

        Returns:
            Valor convertido ou validado.
        """
        if self.action in ("list", "retrieve"):
            return ImportacaoEscolhasListSerializer
        return ImportacaoEscolhasCreateSerializer

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Cria uma nova importação de escolhas.

        Args:
            request: Requisição HTTP recebida.
            *args: Argumentos posicionais variáveis.
            **kwargs: Argumentos nomeados variáveis.

        Returns:
            Resposta HTTP com os dados serializados.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        processo_uuid = serializer.validated_data.get("processo_uuid")
        processo_id = serializer.validated_data.get("processo_id")
        concurso_uuid = serializer.validated_data.get("concurso_uuid")
        if not processo_id:
            processo_id = 819
            logger.info(
                f"Usando processo_id fixo (819) para processo_uuid={processo_uuid}"  # noqa: E501
            )
        try:
            instance = ImportacaoEscolhasService.processar(
                processo_uuid=processo_uuid,
                processo_id=processo_id,
                concurso_uuid=concurso_uuid,
                modo=MODO_IMPORTACAO_MANUAL,
            )
        except ApiProdamError as exc:
            return Response(
                {"detail": exc.mensagem},
                status=exc.status_code or status.HTTP_400_BAD_REQUEST,
            )
        except ApiEscolhasError as exc:
            resposta = {
                "detail": exc.mensagem
                or "Falha ao processar importação de escolhas",
                "detalhes": exc.detalhes or str(exc),
            }
            if exc.code:
                resposta["code"] = exc.code
            return Response(
                resposta, status=exc.status_code or status.HTTP_400_BAD_REQUEST
            )
        except RequestException as exc:
            return Response(
                {"detail": f"Erro ao processar importação: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Erro ao processar importação: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer_response = ImportacaoEscolhasListSerializer(instance)
        headers = self.get_success_headers(serializer_response.data)
        return Response(
            serializer_response.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=["get"], url_path="erros")
    def listar_erros(self, request: Any) -> Any:
        """Lista erros.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Valor convertido ou validado.
        """
        importacao_uuid = request.query_params.get("importacao_uuid", None)
        itens = ImportacaoErroRepository.listar_por_modelo_e_uuid(
            ImportacaoEscolhas, importacao_uuid
        )
        return Response(itens, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="erros/download")
    def download_erros(self, request: Any) -> Any:
        """Download dos erros de importação de escolhas em formato texto.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Valor convertido ou validado.
        """
        importacao_uuid = request.query_params.get("importacao_uuid", None)
        itens = ImportacaoErroRepository.listar_por_modelo_e_uuid(
            ImportacaoEscolhas, importacao_uuid
        )
        linhas = []
        for item in itens:
            erros = item.get("erros") or ""
            if erros:
                partes_erro = erros.split(" | ")
                for parte in partes_erro:
                    if ":" in parte:
                        titulo, conteudo = parte.split(":", 1)
                        linhas.append(
                            f"**{titulo.strip()}:** {conteudo.strip()}"
                        )
                    else:
                        linhas.append(parte)
                linhas.append("")
        conteudo = "\n".join(linhas).rstrip("\n")
        resp = HttpResponse(conteudo, content_type="text/plain; charset=utf-8")
        agora = datetime.now().strftime("%Y%m%d_%H%M%S")
        resp["Content-Disposition"] = (
            f'attachment; filename="escolhas_erros_{agora}.txt"'
        )
        return resp

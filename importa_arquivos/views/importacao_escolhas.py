"""Módulo views/importacao_escolhas."""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime
from typing import Any

from django.conf import settings
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from requests.exceptions import RequestException
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import ImportacaoEscolhas
from ..serializers import (
    ImportacaoErrosListSerializer,
    ImportacaoEscolhasCreateSerializer,
    ImportacaoEscolhasListSerializer,
    queryset_erros_por_modelo,
)
from ..services.api_escolhas import ApiEscolhasService
from ..services.api_prodam import ApiProdamService
from ..services.erros import registrar_erro
from ..services.exceptions import ApiEscolhasException
from ..utils import CustomPagination

logger = logging.getLogger(__name__)


class ImportacaoEscolhasViewSet(viewsets.ModelViewSet):
    """ViewSet para o recurso ImportacaoEscolhas."""

    queryset = ImportacaoEscolhas.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["processo_uuid", "status", "processo_id"]
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
        instance = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid,
            processo_id=processo_id,
            concurso_uuid=concurso_uuid,
            status="PROCESSANDO",
        )
        try:
            logger.info(f"Consultando API externa: processo_id={processo_id}")
            resposta_api = (
                ApiProdamService().consultar_resultado_convocacao_ingresso(
                    processo_id=processo_id
                )
            )
            if resposta_api.get("retorno") != "TRUE":
                mensagem_erro = resposta_api.get(
                    "mensagem", "Erro desconhecido na API PRODAM"
                )
                logger.error(f"API PRODAM retornou erro: {mensagem_erro}")
                instance.status = "ERRO"
                instance.save()
                registrar_erro(
                    instance,
                    mensagem="Erro na resposta da API PRODAM",
                    detalhes=mensagem_erro,
                )
                return Response(
                    {"detail": f"Erro na API PRODAM: {mensagem_erro}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            dados_prodam = resposta_api.get(
                "lstDadosResultadoConvocacaoIngresso", []
            )
            instance.dados_prodam = dados_prodam
            instance.save(update_fields=["dados_prodam"])
            if not dados_prodam:
                logger.warning("API PRODAM retornou lista vazia")
                instance.status = "CONCLUIDO"
                instance.save()
                serializer_response = ImportacaoEscolhasListSerializer(
                    instance
                )
                return Response(
                    serializer_response.data, status=status.HTTP_201_CREATED
                )
            logger.info(
                f"Enviando {len(dados_prodam)} registros para MS-Escolhas"
            )
            api_escolhas_service = ApiEscolhasService(
                base_url=settings.ESCOLHA_API_URL,
                timeout_seconds=settings.ESCOLHA_API_TIMEOUT,
            )
            api_escolhas_service.enviar_escolhas_prodam(
                processo_uuid=processo_uuid,
                concurso_uuid=concurso_uuid,
                dados_prodam=dados_prodam,
                importacao_obj=instance,
            )
            instance.status = "CONCLUIDO"
            instance.save()
            logger.info(
                f"Importação concluída com sucesso: {len(dados_prodam)} registros"  # noqa: E501
            )
        except ApiEscolhasException as exc:
            logger.error(
                f"Erro da API de escolhas durante importação: {exc}",
                exc_info=True,
            )
            instance.status = "ERRO"
            instance.save()
            with contextlib.suppress(Exception):
                registrar_erro(
                    instance,
                    mensagem="Erro durante importação de escolhas",
                    detalhes=exc.detalhes or str(exc),
                    exc=exc,
                )
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
            logger.error(
                f"Erro de request durante importação de escolhas: {exc}",
                exc_info=True,
            )
            instance.status = "ERRO"
            instance.save()
            with contextlib.suppress(Exception):
                registrar_erro(
                    instance,
                    mensagem="Erro durante importação de escolhas",
                    detalhes=str(exc),
                    exc=exc,
                )
            return Response(
                {"detail": f"Erro ao processar importação: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as exc:
            logger.error(
                f"Erro durante importação de escolhas: {exc}", exc_info=True
            )
            instance.status = "ERRO"
            instance.save()
            with contextlib.suppress(Exception):
                registrar_erro(
                    instance,
                    mensagem="Erro durante importação de escolhas",
                    detalhes=str(exc),
                    exc=exc,
                )
            return Response(
                {"detail": f"Erro ao processar importação: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        instance.refresh_from_db()
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
        qs = queryset_erros_por_modelo(
            ImportacaoEscolhas, importacao_uuid=importacao_uuid
        ).select_related("content_type")
        serializer = ImportacaoErrosListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="erros/download")
    def download_erros(self, request: Any) -> Any:
        """Download dos erros de importação de escolhas em formato texto.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Valor convertido ou validado.
        """
        importacao_uuid = request.query_params.get("importacao_uuid", None)
        qs = queryset_erros_por_modelo(
            ImportacaoEscolhas, importacao_uuid=importacao_uuid
        ).select_related("content_type")
        serializer = ImportacaoErrosListSerializer(qs, many=True)
        linhas = []
        for item in serializer.data:
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

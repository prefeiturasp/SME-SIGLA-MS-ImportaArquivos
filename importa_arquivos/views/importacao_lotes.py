"""ViewSet de importação de arquivos de lotes de classificação (SIGPEC).

- create: recebe arquivo TXT + concurso_uuid, valida, chama API de candidatos e
retorna resultado.
- list: listagem paginada com filtros.
- retrieve: detalhe de um registro.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import ImportacaoLotes
from ..serializers import (
    ImportacaoLotesCreateSerializer,
    ImportacaoLotesListSerializer,
)
from ..services.api_candidatos import ApiCandidatosService
from ..services.exceptions import (
    BaseImportacaoException,
    ErrosValidacaoLotesException,
    ImportacaoBadRequestException,
    ImportacaoServiceUnavailableException,
)
from ..services.importacao_lotes import validar_txt_lotes
from ..utils import CustomPagination

logger = logging.getLogger(__name__)


class ImportacaoLotesViewSet(viewsets.ModelViewSet):
    """ViewSet para importação de arquivos de lotes de classificação."""

    queryset = ImportacaoLotes.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "nome_arquivo",
        "status",
        "concurso_uuid",
        "concurso_nome",
    ]
    search_fields = ["concurso_uuid", "concurso_nome"]
    ordering_fields = ["nome_arquivo", "status", "criado_em"]
    ordering = ["-criado_em"]
    pagination_class = CustomPagination
    lookup_field = "uuid"

    def get_serializer_class(self) -> Any:
        """Executa get serializer class.

        Args:
            self: Instância do objeto.

        Returns:
            Valor calculado para o campo ou propriedade.

        Raises:
            Nenhuma exceção específica documentada.
        """
        if self.action in ("list", "retrieve"):
            return ImportacaoLotesListSerializer
        return ImportacaoLotesCreateSerializer

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Executa create.

        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            *args: Argumentos posicionais variáveis.
            **kwargs: Argumentos nomeados variáveis.

        Returns:
            Resposta HTTP com os dados serializados.

        Raises:
            Nenhuma exceção específica documentada.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        try:
            registros = validar_txt_lotes(
                instance.arquivo, importacao_obj=instance
            )
        except ErrosValidacaoLotesException as exc:
            return Response(
                {"mensagem": exc.mensagem, "detail": exc.detalhes},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except BaseImportacaoException as exc:
            return Response(
                {"mensagem": exc.mensagem, "detail": exc.detalhes},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error(
                "Erro inesperado ao validar arquivo de lotes: %s", exc
            )
            return Response(
                {
                    "mensagem": "Erro ao validar arquivo de lotes.",
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.detalhes = registros
        concurso_uuid = str(instance.concurso_uuid)
        try:
            total = ApiCandidatosService(
                base_url=settings.CANDIDATOS_API_URL
            ).salvar_lotes(
                concurso_uuid=concurso_uuid,
                lotes=registros,
                importacao_obj=instance,
            )
        except (
            ImportacaoServiceUnavailableException,
            ImportacaoBadRequestException,
            Exception,
        ) as exc:
            logger.error(
                "Erro ao fazer request para salvar os lotes no serviço de candidatos: %s",  # noqa: E501
                exc,
            )
            return Response(
                {
                    "mensagem": "Erro ao fazer request para salvar os lotes no serviço de candidatos.",  # noqa: E501
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = "CONCLUIDO"
        instance.total_atualizados = total
        instance.save(
            update_fields=["status", "total_atualizados", "detalhes"]
        )
        instance.refresh_from_db()
        response_serializer = ImportacaoLotesListSerializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

"""View base abstrata para exportação de dados.

Centraliza list/create/retrieve, get_serializer_class, list com query params
(processo_uuid, cargo_uuid, concurso_uuid) para resposta em arquivo, action
download e tratamento de exceções (404/502).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from importa_arquivos.utils import CustomPagination

from ..services.exceptions import (
    ExportacaoBadRequestException,
    ExportacaoNotFoundException,
    ExportacaoServiceUnavailableException,
)

logger = logging.getLogger(__name__)


def _sanitizar_nome_arquivo(texto: str, max_len: int = 80) -> str:
    """Remove caracteres inválidos para nome de arquivo e limita tamanho.

    Args:
        texto: Parâmetro texto.
        max_len: Parâmetro max len.

    Returns:
        Texto resultante da operação.

    Raises:
        Nenhuma exceção específica documentada.
    """
    if not texto or not isinstance(texto, str):
        return "arquivo"
    s = re.sub("[^\\w\\s\\-]", "", texto, flags=re.UNICODE)
    s = re.sub("\\s+", "_", s.strip())
    return (s[:max_len] if len(s) > max_len else s) or "arquivo"


class BaseExportacaoViewSet(viewsets.ModelViewSet):
    """ViewSet base abstrata para exportação."""

    list_serializer_class = None
    create_serializer_class = None
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "processo_uuid",
        "cargo_uuid",
        "concurso_uuid",
        "concurso_nome",
    ]
    search_fields = ["concurso_nome"]
    ordering_fields = [
        "criado_em",
        "atualizado_em",
        "processo_uuid",
        "cargo_uuid",
    ]
    ordering = ["-criado_em"]
    pagination_class = CustomPagination

    @staticmethod
    def sanitizar_nome_arquivo(texto: str, max_len: int = 80) -> str:
        """Remove caracteres inválidos para nome de arquivo e limita tamanho.

        Args:
            texto: Parâmetro texto.
            max_len: Parâmetro max len.

        Returns:
            Texto resultante da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return _sanitizar_nome_arquivo(texto, max_len)

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
            return self.list_serializer_class
        return self.create_serializer_class

    def list(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Listagem paginada ou, se processo_uuid, cargo_uuid e cargo_codigo.

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
        processo_uuid = request.query_params.get("processo_uuid", "").strip()
        cargo_uuid = request.query_params.get("cargo_uuid", "").strip()
        concurso_uuid = (
            request.query_params.get("concurso_uuid", "").strip() or None
        )
        processo_nome = (
            request.query_params.get("processo_nome", "").strip() or None
        )
        cargo_nome = request.query_params.get("cargo_nome", "").strip() or None
        cargo_codigo_raw = (
            request.query_params.get("cargo_codigo", "").strip() or None
        )
        if processo_uuid and cargo_uuid:
            if not cargo_codigo_raw:
                return Response(
                    {
                        "detail": "Para download direto, envie processo_uuid, cargo_uuid e cargo_codigo na query."  # noqa: E501
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                cargo_codigo = int(cargo_codigo_raw)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "cargo_codigo na query deve ser numérico."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return self.gerar_arquivo(
                processo_uuid,
                cargo_uuid,
                concurso_uuid=concurso_uuid,
                processo_nome=processo_nome,
                cargo_nome=cargo_nome,
                cargo_codigo=cargo_codigo,
            )  # type: ignore[call-arg]
        return super().list(request, *args, **kwargs)

    def gerar_arquivo(self, instance: Any) -> None:
        """Gera resposta de arquivo para os UUIDs dados.

        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.

        Returns:
            Não retorna valor.

        Raises:
            NotImplementedError: Se ocorrer erro nesta operação.
        """
        raise NotImplementedError("Subclasse deve implementar gerar_arquivo.")

    def executar_exportacao(self, instance: Any) -> None:
        """Executa a exportação após create (ex.: chamar serviço com.

        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.

        Returns:
            Não retorna valor.

        Raises:
            NotImplementedError: Se ocorrer erro nesta operação.
        """
        raise NotImplementedError(
            "Subclasse deve implementar executar_exportacao."
        )

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
            self.executar_exportacao(instance)
        except ExportacaoBadRequestException as exc:
            logger.warning(
                "Erro de validação (400) na exportação %s: %s",
                instance.uuid,
                exc.mensagem,
            )
            return Response(
                {"mensagem": exc.mensagem, "detail": exc.detalhes},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ExportacaoNotFoundException as exc:
            logger.warning(
                "Dados não encontrados (404) na exportação %s: %s",
                instance.uuid,
                exc.mensagem,
            )
            return Response(
                {"mensagem": exc.mensagem, "detail": exc.detalhes},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ExportacaoServiceUnavailableException as exc:
            logger.error(
                "Serviço indisponível (502) na exportação %s: %s",
                instance.uuid,
                exc.mensagem,
            )
            return Response(
                {"mensagem": exc.mensagem, "detail": exc.detalhes},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as exc:
            logger.exception(
                "Erro interno (500) inesperado na exportação %s: %s",
                instance.uuid,
                exc,
            )
            return Response(
                {
                    "mensagem": "Erro interno ao gerar exportação.",
                    "detail": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return self.gerar_arquivo(instance)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request: Any, uuid: Any = None) -> Any:
        """Retorna o arquivo da exportação. Se o registro tiver.

        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            uuid: Parâmetro uuid.

        Returns:
            Resultado da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        instance = self.get_object()
        return self.gerar_arquivo(instance)

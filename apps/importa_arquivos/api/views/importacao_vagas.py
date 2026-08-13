"""ViewSet de importação de arquivo de vagas."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from importa_arquivos.models import ImportacaoArquivoVagas
from importa_arquivos.repository import (
    ImportacaoArquivoVagasRepository,
    ImportacaoErroRepository,
)
from importa_arquivos.serializers import (
    ImportacaoArquivoVagasCreateSerializer,
    ImportacaoArquivoVagasListSerializer,
)
from importa_arquivos.services.api_escolhas import ApiEscolhasService
from importa_arquivos.services.exceptions import (
    ApiEscolhasError,
    ColunaCSVInvalidaError,
    LayoutNaoConfiguradoError,
    LeituraCSVError,
    TipoUEDesabilitadoError,
)
from importa_arquivos.services.validacao_vagas import validar_csv_vagas
from importa_arquivos.utils import CustomPagination


class ImportacaoArquivoVagasViewSet(viewsets.ModelViewSet):
    """ViewSet para o recurso ImportacaoArquivoVagas."""

    queryset = ImportacaoArquivoVagas.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "nome_arquivo",
        "status",
        "processo_uuid",
        "processo_nome",
    ]
    search_fields = ["processo_uuid", "processo_nome"]
    ordering_fields = ["nome_arquivo", "status", "criado_em"]
    ordering = ["-criado_em"]
    pagination_class = CustomPagination

    def get_serializer_class(self) -> Any:
        """Retorna serializer class de acordo com a action."""
        if self.action in ("list", "retrieve"):
            return ImportacaoArquivoVagasListSerializer
        return ImportacaoArquivoVagasCreateSerializer

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Cria uma nova importação de vagas."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer.validated_data.get("processo_uuid") or request.data.get(
            "processo_uuid"
        )
        serializer.validated_data.get("processo_nome") or request.data.get(
            "processo_nome"
        )
        try:
            registros, estrutura = validar_csv_vagas(
                instance.arquivo, importacao_obj=instance
            )
        except (
            ColunaCSVInvalidaError,
            LayoutNaoConfiguradoError,
            LeituraCSVError,
        ) as exc:
            mensagem = getattr(exc, "mensagem", "Erro ao validar CSV.")
            detalhes = getattr(exc, "detalhes", str(exc))
            logging.error(
                "Erro na validação do CSV de Vagas: %s - %s",
                mensagem,
                detalhes,
            )
            return Response(
                {"detail": mensagem, "detalhes": detalhes},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logging.error("Erro inesperado na validação do CSV: %s", exc)
            return Response(
                {"detail": "Erro ao validar CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ApiEscolhasService().enviar_vagas(
                registros=registros,
                estrutura=estrutura,
                processo_uuid=(
                    str(instance.processo_uuid)
                    if instance.processo_uuid
                    else ""
                ),
                processo_nome=(
                    str(instance.processo_nome)
                    if instance.processo_nome
                    else ""
                ),
                concurso_uuid=(
                    str(instance.concurso_uuid)
                    if instance.concurso_uuid
                    else ""
                ),
                importacao_obj=instance,
            )
        except TipoUEDesabilitadoError as exc:
            logging.error("Tipo UE desabilitado ao enviar dados: %s", exc)
            return Response(
                {"detail": str(exc), "code": "TIPO_UE_DESABILITADO"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ApiEscolhasError as exc:
            ImportacaoArquivoVagasRepository.recarregar(instance)
            payload = {
                "detail": exc.mensagem,
                "detalhes": exc.detalhes or str(exc),
                "status_code": exc.status_code,
            }
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logging.error("Erro inesperado ao enviar vagas: %s", exc)
            return Response(
                {"detail": "Erro ao enviar vagas para API externa."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ImportacaoArquivoVagasRepository.recarregar(instance)
        serializer = ImportacaoArquivoVagasListSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=["get"], url_path="erros/download")
    def download_erros(self, request: Any) -> Any:
        """Download dos erros de importação de vagas em formato texto.

        Returns:
            Retorna o arquivo de erros em formato texto.
        """
        importacao_uuid = request.query_params.get("importacao_uuid", None)
        itens = ImportacaoErroRepository.listar_por_modelo_e_uuid(
            ImportacaoArquivoVagas, importacao_uuid
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
            f'attachment; filename="vagas_erros_{agora}.txt"'
        )
        return resp

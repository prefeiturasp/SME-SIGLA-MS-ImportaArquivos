"""
ViewSet de importação de arquivos de lotes de classificação (SIGPEC).

- create: recebe arquivo TXT + concurso_uuid, valida, chama API de candidatos e retorna resultado.
- list: listagem paginada com filtros.
- retrieve: detalhe de um registro.
"""
import logging

from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..utils import CustomPagination
from ..models import ImportacaoLotes
from ..serializers import ImportacaoLotesCreateSerializer, ImportacaoLotesListSerializer
from ..services.importacao_lotes import validar_txt_lotes
from ..services.api_candidatos import ApiCandidatosService
from ..services.erros import registrar_erro
from ..services.exceptions import (
    BaseImportacaoException,
    ImportacaoBadRequestException,
    ImportacaoServiceUnavailableException,
)

logger = logging.getLogger(__name__)


def _montar_resumo_erros_linha(erros_por_linha: list[dict]) -> str:
    if not erros_por_linha:
        return ''

    linhas: list[str] = []
    for erro in erros_por_linha:
        linha = erro.get('linha')
        identificacao = erro.get('identificacao')
        mensagem = erro.get('mensagem') or 'Erro nao identificado.'
        linhas.append(f"Linha {linha} | identificacao={identificacao}: {mensagem}")

    return ' | '.join(linhas)


class ImportacaoLotesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para importação de arquivos de lotes de classificação (SIGPEC).
    """
    queryset = ImportacaoLotes.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nome_arquivo', 'status', 'concurso_uuid', 'concurso_nome']
    search_fields = ['concurso_uuid', 'concurso_nome']
    ordering_fields = ['nome_arquivo', 'status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ImportacaoLotesListSerializer
        return ImportacaoLotesCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # 1. Validar e parsear o arquivo TXT
        # Exceções estruturais são capturadas pelo decorator @captura_erros_importacao,
        # que já persiste em ImportacaoErro e seta status=ERRO.
        try:
            registros, erros_por_linha = validar_txt_lotes(instance.arquivo, importacao_obj=instance)
        except BaseImportacaoException as exc:
            return Response(
                {'detail': exc.mensagem, 'detalhes': exc.detalhes},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error('Erro inesperado ao validar arquivo de lotes: %s', exc)
            return Response({'detail': 'Erro ao validar arquivo de lotes.'}, status=status.HTTP_400_BAD_REQUEST)

        # Erros de linha (validação Pydantic) não são exceções — registrar explicitamente.
        if erros_por_linha:
            mensagem = f'Arquivo possui {len(erros_por_linha)} erro(s) de validação.'
            resumo_linhas = _montar_resumo_erros_linha(erros_por_linha)
            registrar_erro(instance, mensagem=mensagem, detalhes=resumo_linhas)
            return Response(
                {'detail': mensagem, 'erros_por_linha': erros_por_linha},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Salvar registros parseados como detalhes da importação
        instance.detalhes = registros

        # 2. Enviar para a API de candidatos
        concurso_uuid = str(instance.concurso_uuid)
        try:
            total = ApiCandidatosService(
                base_url=settings.CANDIDATOS_API_URL,
            ).salvar_lotes(
                concurso_uuid=concurso_uuid,
                lotes=registros,
            )
        except ImportacaoBadRequestException as exc:
            logger.error('Erro de requisição ao salvar lotes: %s', exc)
            erros_por_linha = getattr(exc, 'erros_por_linha', []) or []
            resumo_linhas = _montar_resumo_erros_linha(erros_por_linha)
            registrar_erro(instance, mensagem=exc.mensagem, detalhes=resumo_linhas or exc.detalhes)
            instance.detalhes = {
                'registros_processados': registros,
                'erros_por_linha': erros_por_linha,
            }
            instance.save(update_fields=['detalhes'])
            return Response({'detail': exc.mensagem}, status=status.HTTP_400_BAD_REQUEST)
        except ImportacaoServiceUnavailableException as exc:
            logger.error('Servico de candidatos indisponivel ao salvar lotes: %s', exc)
            registrar_erro(instance, mensagem=exc.mensagem, detalhes=exc.detalhes)
            return Response({'detail': exc.mensagem}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error('Erro inesperado ao salvar lotes: %s', exc, exc_info=True)
            registrar_erro(instance, mensagem='Erro inesperado ao salvar lotes.', exc=exc)
            return Response({'detail': 'Erro inesperado ao salvar lotes.'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = 'CONCLUIDO'
        instance.total_atualizados = total
        instance.save(update_fields=['status', 'total_atualizados', 'detalhes'])
        instance.refresh_from_db()
        response_serializer = ImportacaoLotesListSerializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

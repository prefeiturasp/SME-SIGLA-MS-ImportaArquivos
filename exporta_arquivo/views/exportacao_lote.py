"""Views para exportação de lotes e gerenciamento do cabeçalho.

ExportacaoLoteViewSet:
  - POST /exportacao/lote/  → exporta lote; retorna arquivo .txt (200) ou
  arquivo de erro (422)
  - GET  /exportacao/lote/  → lista histórico paginado
  - GET  /exportacao/lote/<uuid>/         → detalhe
  - GET  /exportacao/lote/<uuid>/download/ → redownload do arquivo

CabecalhoExportacaoLoteViewSet:
  - CRUD completo para edição do cabeçalho configurável
"""
from __future__ import annotations
from typing import Any
import logging
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from importa_arquivos.utils import CustomPagination
from ..models import CabecalhoExportacaoLote, ExportacaoLote
from ..serializers import CabecalhoExportacaoLoteSerializer, ExportacaoLoteCreateSerializer, ExportacaoLoteListSerializer
from ..services.exceptions import ExportacaoLoteIncompletaException
from ..services.exportacao_lote import exportar_lote
from .base_exportacao import _sanitizar_nome_arquivo
logger = logging.getLogger(__name__)

class ExportacaoLoteViewSet(viewsets.ModelViewSet):
    """ViewSet para exportação de lotes."""
    queryset = ExportacaoLote.objects.all()
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['concurso_uuid', 'lote_uuid', 'concurso_nome', 'numero_lote', 'codigo_cargo']
    search_fields = ['concurso_nome']
    ordering_fields = ['criado_em', 'atualizado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def get_serializer_class(self) -> Any:
        """Executa get serializer class.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Valor calculado para o campo ou propriedade.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        if self.action in ('list', 'retrieve'):
            return ExportacaoLoteListSerializer
        return ExportacaoLoteCreateSerializer

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
            conteudo = exportar_lote(instance)
        except ExportacaoLoteIncompletaException as exc:
            logger.warning('Exportação incompleta (422) para o lote %s: %s', instance.uuid, exc.mensagem)
            nomes = exc.candidatos_sem_escolha
            conteudo_erro = self._gerar_conteudo_erro(nomes, instance)
            lote_id = instance.numero_lote if instance.numero_lote is not None else str(instance.lote_uuid)
            nome_arquivo_erro = f'candidatos_sem_escolha_lote_{_sanitizar_nome_arquivo(str(lote_id))}.txt'
            instance.conteudo_arquivo = conteudo_erro
            instance.nome_arquivo = nome_arquivo_erro
            instance.status = 'ATENCAO'
            instance.save(update_fields=['conteudo_arquivo', 'nome_arquivo', 'status'])
            response = HttpResponse(conteudo_erro.encode('utf-8'), content_type='text/plain; charset=utf-8', status=422)
            response['Content-Disposition'] = f'attachment; filename="{nome_arquivo_erro}"'
            return response
        except Exception as exc:
            logger.warning(f'Exportação: {instance.uuid} | {exc.mensagem} | {exc.detalhes}')  # type: ignore[attr-defined]
            instance.status = 'ERRO'
            instance.save(update_fields=['status'])
            return Response({'mensagem': exc.mensagem, 'detail': exc.detalhes}, status=status.HTTP_400_BAD_REQUEST)  # type: ignore[attr-defined]
        lote_id = instance.numero_lote if instance.numero_lote is not None else str(instance.lote_uuid)
        nome_arquivo = f'exportacao_lote_{_sanitizar_nome_arquivo(str(lote_id))}.txt'
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.status = 'SUCESSO'
        instance.save(update_fields=['conteudo_arquivo', 'nome_arquivo', 'status'])
        response = HttpResponse(conteudo.encode('utf-8'), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
        return response

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request: Any, uuid: Any=None) -> Any:
        """Redownload do arquivo exportado (sucesso ou erro).
        
        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            uuid: Parâmetro uuid da operação.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        instance = self.get_object()
        if not instance.conteudo_arquivo:
            return Response({'detail': 'Arquivo não disponível para este registro.'}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(instance.conteudo_arquivo.encode('utf-8'), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{instance.nome_arquivo}"'
        return response

    @staticmethod
    def _gerar_conteudo_erro(nomes: list, instance: ExportacaoLote) -> str:
        """Executa  gerar conteudo erro.
        
        Args:
            nomes: Parâmetro nomes da operação.
            instance: Instância do modelo em atualização.
        
        Returns:
            Texto resultante da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        lote_id = instance.numero_lote if instance.numero_lote is not None else instance.lote_uuid
        linhas = [f'Candidatos sem escolha realizada no lote {lote_id}:']
        for nome in nomes:
            linhas.append(f'- {nome}')
        return '\n'.join(linhas) + '\n'

class CabecalhoExportacaoLoteViewSet(viewsets.ModelViewSet):
    """CRUD para o cabeçalho configurável de exportação de lotes."""
    queryset = CabecalhoExportacaoLote.objects.all()
    serializer_class = CabecalhoExportacaoLoteSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['ativo']
    ordering = ['-criado_em']

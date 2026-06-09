"""Módulo views/importacao_habilitados."""
from __future__ import annotations
from typing import Any
import logging
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import ImportacaoArquivoHabilitado
from ..serializers import ImportacaoArquivoHabilitadosCreateSerializer, ImportacaoArquivoHabilitadosListSerializer, ImportacaoErrosListSerializer, queryset_erros_por_modelo
from ..services.api_candidatos import ApiCandidatosService
from ..services.exceptions import ApiCandidatosException, CargoConcursoInvalidoException, ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException
from ..services.validacao_habilitados import validar_csv_habilitados

class ImportacaoArquivoHabilitadosViewSet(viewsets.ModelViewSet):
    """Define ImportacaoArquivoHabilitadosViewSet."""
    queryset = ImportacaoArquivoHabilitado.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nome_arquivo', 'status', 'concurso_uuid', 'concurso_nome']
    search_fields = ['concurso_uuid', 'concurso_nome']
    ordering_fields = ['nome_arquivo', 'status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = None

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
            return ImportacaoArquivoHabilitadosListSerializer
        return ImportacaoArquivoHabilitadosCreateSerializer

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
        serializer.validated_data.get('concurso_uuid') or request.data.get('concurso_uuid')
        serializer.validated_data.get('concurso_nome') or request.data.get('concurso_nome')
        try:
            registros, estrutura = validar_csv_habilitados(instance.arquivo, importacao_obj=instance)
        except (ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException, CargoConcursoInvalidoException) as exc:
            mensagem = getattr(exc, 'mensagem', 'Erro ao validar arquivo de Habilitados')
            detalhes = getattr(exc, 'detalhes', str(exc))
            logging.error('Erro na validação do CSV de Habilitados: %s - %s', mensagem, detalhes)
            return Response({'detail': mensagem, 'detalhes': detalhes}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logging.error('Erro inesperado na validação do CSV: %s', exc)
            return Response({'detail': 'Erro ao validar arquivo de Habilitados.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ApiCandidatosService(base_url=settings.CANDIDATOS_API_URL).enviar_habilitados(registros=registros, estrutura=estrutura, concurso_uuid=str(instance.concurso_uuid) if instance.concurso_uuid else '', concurso_nome=str(instance.concurso_nome) if instance.concurso_nome else '', importacao_obj=instance)
        except ApiCandidatosException as exc:
            instance.refresh_from_db()
            payload = {'detail': exc.mensagem, 'detalhes': exc.detalhes or str(exc), 'status_code': exc.status_code}
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logging.error('Erro inesperado ao enviar candidatos: %s', exc)
            return Response({'detail': 'Erro ao enviar candidatos para API externa.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            instance.status = 'CONCLUIDO'
            instance.save(update_fields=['status'])
        instance.refresh_from_db()
        serializer = ImportacaoArquivoHabilitadosListSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='erros/download')
    def download_erros(self, request: Any) -> Any:
        """Executa download erros.
        
        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        importacao_uuid = request.query_params.get('importacao_uuid', None)
        qs = queryset_erros_por_modelo(ImportacaoArquivoHabilitado, importacao_uuid=importacao_uuid).select_related('content_type')
        serializer = ImportacaoErrosListSerializer(qs, many=True)
        linhas = []
        for item in serializer.data:
            erros = item.get('erros') or ''
            if erros:
                partes_erro = erros.split(' | ')
                for parte in partes_erro:
                    if ':' in parte:
                        titulo, conteudo = parte.split(':', 1)
                        linhas.append(f'**{titulo.strip()}:** {conteudo.strip()}')
                    else:
                        linhas.append(parte)
                linhas.append('')
        conteudo = '\n'.join(linhas).rstrip('\n')
        resp = HttpResponse(conteudo, content_type='text/plain; charset=utf-8')
        agora = datetime.now().strftime('%Y%m%d_%H%M%S')
        resp['Content-Disposition'] = f'attachment; filename="habilitados_erros_{agora}.txt"'
        return resp

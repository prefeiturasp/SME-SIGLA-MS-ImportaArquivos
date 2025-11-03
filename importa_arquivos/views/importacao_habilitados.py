from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from ..services.validacao_habilitados import validar_csv_habilitados
from ..services.api_candidatos import ApiCandidatosService
from ..services.exceptions import ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException
from ..models import ImportacaoArquivoHabilitado
from ..serializers import (
    ImportacaoArquivoHabilitadosCreateSerializer, 
    ImportacaoArquivoHabilitadosListSerializer,
)
from ..utils import CustomPagination
from rest_framework.decorators import action
from django.http import HttpResponse
from datetime import datetime
from ..serializers import ImportacaoErrosListSerializer, queryset_erros_por_modelo
from ..models import ImportacaoErro


class ImportacaoArquivoHabilitadosViewSet(viewsets.ModelViewSet):
    queryset = ImportacaoArquivoHabilitado.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nome_arquivo', 'status', 'concurso_uuid', 'concurso_nome']
    search_fields = ['concurso_uuid', 'concurso_nome']
    ordering_fields = ['nome_arquivo', 'status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ImportacaoArquivoHabilitadosListSerializer
        return ImportacaoArquivoHabilitadosCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        concurso_uuid = serializer.validated_data.get('concurso_uuid') or request.data.get('concurso_uuid')
        concurso_nome = serializer.validated_data.get('concurso_nome') or request.data.get('concurso_nome')

        try:
            registros, estrutura = validar_csv_habilitados(instance.arquivo, importacao_obj=instance)
        except (ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException) as exc:
            mensagem = getattr(exc, 'mensagem', 'Erro ao validar arquivo de Habilitados')
            detalhes = getattr(exc, 'detalhes', str(exc))
            logging.error('Erro na validação do CSV de Habilitados: %s - %s', mensagem, detalhes)
            return Response({'detail': mensagem, 'detalhes': detalhes}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logging.error('Erro inesperado na validação do CSV: %s', exc)
            return Response({'detail': 'Erro ao validar arquivo de Habilitados.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ApiCandidatosService(
                base_url=settings.CANDIDATOS_API_URL,
            ).enviar_habilitados(
                registros=registros,
                estrutura=estrutura,
                concurso_uuid=str(instance.concurso_uuid) if instance.concurso_uuid else '',
                concurso_nome=str(instance.concurso_nome) if instance.concurso_nome else '',
                importacao_obj=instance,
            )
        except Exception as exc:
            logging.error('Falha ao enviar dados para API externa: %s', exc)
            instance.refresh_from_db()

        instance.refresh_from_db()
        serializer = ImportacaoArquivoHabilitadosListSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='erros/download')
    def download_erros(self, request):
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
                        linhas.append(f"**{titulo.strip()}:** {conteudo.strip()}")
                    else:
                        linhas.append(parte)
                linhas.append('')
        conteudo = "\n".join(linhas).rstrip('\n')
        resp = HttpResponse(conteudo, content_type='text/plain; charset=utf-8')
        agora = datetime.now().strftime('%Y%m%d_%H%M%S')
        resp['Content-Disposition'] = f'attachment; filename="habilitados_erros_{agora}.txt"'
        return resp

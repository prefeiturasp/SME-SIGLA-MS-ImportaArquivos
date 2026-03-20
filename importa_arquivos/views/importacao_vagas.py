from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from django.conf import settings

from ..models import ImportacaoArquivoVagas
from ..serializers import (
    ImportacaoArquivoVagasCreateSerializer,
    ImportacaoArquivoVagasListSerializer,
)
from ..services.validacao_vagas import validar_csv_vagas
from ..services.api_escolhas import ApiEscolhasService
from ..services.exceptions import ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException
from ..services.exceptions import TipoUEDesabilitadoException
from ..utils import CustomPagination
from rest_framework.decorators import action
from django.http import HttpResponse
from datetime import datetime
from ..serializers import ImportacaoErrosListSerializer, queryset_erros_por_modelo
from requests.exceptions import HTTPError, RequestException, Timeout


class ImportacaoArquivoVagasViewSet(viewsets.ModelViewSet):
    queryset = ImportacaoArquivoVagas.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nome_arquivo', 'status', 'processo_uuid', 'processo_nome']
    search_fields = ['processo_uuid', 'processo_nome']
    ordering_fields = ['nome_arquivo', 'status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ImportacaoArquivoVagasListSerializer
        return ImportacaoArquivoVagasCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        processo_uuid = serializer.validated_data.get('processo_uuid') or request.data.get('processo_uuid')
        processo_nome = serializer.validated_data.get('processo_nome') or request.data.get('processo_nome')

        try:
            registros, estrutura = validar_csv_vagas(instance.arquivo, importacao_obj=instance)
        except (ColunaCSVInvalidaException, LayoutNaoConfiguradoException, LeituraCSVException) as exc:
            # Mas ainda retornamos resposta HTTP para o cliente
            mensagem = getattr(exc, 'mensagem', 'Erro ao validar CSV.')
            detalhes = getattr(exc, 'detalhes', str(exc))
            logging.error('Erro na validação do CSV de Vagas: %s - %s', mensagem, detalhes)
            return Response({'detail': mensagem, 'detalhes': detalhes}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logging.error('Erro inesperado na validação do CSV: %s', exc)
            return Response({'detail': 'Erro ao validar CSV.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ApiEscolhasService(
                base_url=settings.ESCOLHA_API_URL,
            ).enviar_vagas(
                registros=registros,
                estrutura=estrutura,
                processo_uuid=str(instance.processo_uuid) if instance.processo_uuid else '',
                processo_nome=str(instance.processo_nome) if instance.processo_nome else '',
                importacao_obj=instance,
            )
        except TipoUEDesabilitadoException as exc:
            logging.error('Tipo UE desabilitado ao enviar dados: %s', exc)
            return Response({'detail': str(exc), 'code': 'TIPO_UE_DESABILITADO'}, status=status.HTTP_400_BAD_REQUEST)
        except HTTPError as exc:
            logging.error('Falha ao enviar dados para API externa: %s', exc)
            instance.refresh_from_db()

            status_code = getattr(exc.response, 'status_code', None) or status.HTTP_502_BAD_GATEWAY
            response_data = None
            response_text = ''
            try:
                response_text = exc.response.text if exc.response is not None else str(exc)
            except Exception:
                response_text = str(exc)

            try:
                response_data = exc.response.json() if exc.response is not None else None
            except Exception:
                response_data = None

            detail = 'Falha ao enviar dados para API externa'
            code = None
            detalhes = response_text or str(exc)
            if isinstance(response_data, dict):
                detail = response_data.get('detail') or response_data.get('message') or detail
                code = response_data.get('code')
                detalhes = response_data.get('detalhes') or response_data.get('detail') or detalhes

            payload = {'detail': detail, 'detalhes': detalhes}
            if code:
                payload['code'] = code
            return Response(payload, status=status_code)
        except RequestException as exc:
            logging.error('Falha ao enviar dados para API externa: %s', exc)
            instance.refresh_from_db()
            if isinstance(exc, Timeout):
                return Response(
                    {'detail': 'Timeout ao enviar dados para API externa', 'detalhes': str(exc)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {'detail': 'Falha ao enviar dados para API externa', 'detalhes': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as exc:
            logging.error('Erro inesperado ao enviar dados para API externa: %s', exc)
            instance.refresh_from_db()
            return Response(
                {'detail': 'Erro ao enviar dados para API externa', 'detalhes': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.refresh_from_db()
        serializer = ImportacaoArquivoVagasListSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='erros/download')
    def download_erros(self, request):
        importacao_uuid = request.query_params.get('importacao_uuid', None)
        qs = queryset_erros_por_modelo(ImportacaoArquivoVagas, importacao_uuid=importacao_uuid).select_related('content_type')
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
        resp['Content-Disposition'] = f'attachment; filename="vagas_erros_{agora}.txt"'
        return resp

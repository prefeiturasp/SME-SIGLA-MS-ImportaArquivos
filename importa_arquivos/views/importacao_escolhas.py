from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from django.http import HttpResponse
from datetime import datetime
import logging
from django.conf import settings

from ..models import ImportacaoEscolhas
from ..serializers import (
    ImportacaoEscolhasCreateSerializer,
    ImportacaoEscolhasListSerializer,
    EscolhasImportacaoSerializer,
    ImportacaoErrosListSerializer,
    queryset_erros_por_modelo,
)
from ..services.api_prodam import ApiProdamService
from ..services.api_escolhas import ApiEscolhasService
from ..services.erros import registrar_erro
from ..utils import CustomPagination

logger = logging.getLogger(__name__)


class ImportacaoEscolhasViewSet(viewsets.ModelViewSet):
    queryset = ImportacaoEscolhas.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['processo_uuid', 'status', 'processo_id']
    search_fields = ['processo_uuid']
    ordering_fields = ['status', 'criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ImportacaoEscolhasListSerializer
        return ImportacaoEscolhasCreateSerializer

    def create(self, request, *args, **kwargs):
        """
        Cria uma nova importação de escolhas.
        
        Fluxo:
        1. Valida dados recebidos do front
        2. Cria registro de importação com status PENDENTE
        3. Consulta API externa
        4. Valida resposta da API externa
        5. Transforma dados para formato MS-Escolhas
        6. Envia dados para MS-Escolhas
        7. Atualiza status da importação
        """
        # 1. Validar dados recebidos do front
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Criar registro de importação
        processo_uuid = serializer.validated_data.get('processo_uuid')
        processo_id = serializer.validated_data.get('processo_id')
        concurso_uuid = serializer.validated_data.get('concurso_uuid')
        
        if not processo_id:
            processo_id = 819
            logger.info(f'Usando processo_id fixo (819) para processo_uuid={processo_uuid}')
        
        instance = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid,
            processo_id=processo_id,
            concurso_uuid=concurso_uuid,
            status='PROCESSANDO'
        )
        
        try:
            # 3. Consultar API externa
            logger.info(f'Consultando API externa: processo_id={processo_id}')
            resposta_api = ApiProdamService().consultar_resultado_convocacao_ingresso(
                processo_id=processo_id
            )
            
            # Verificar se a resposta foi bem-sucedida
            if resposta_api.get('retorno') != 'TRUE':
                mensagem_erro = resposta_api.get('mensagem', 'Erro desconhecido na API PRODAM')
                logger.error(f'API PRODAM retornou erro: {mensagem_erro}')
                instance.status = 'ERRO'
                instance.save()
                registrar_erro(
                    instance,
                    mensagem='Erro na resposta da API PRODAM',
                    detalhes=mensagem_erro
                )
                return Response(
                    {'detail': f'Erro na API PRODAM: {mensagem_erro}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. Obter lista de dados
            dados_prodam = resposta_api.get('lstDadosResultadoConvocacaoIngresso', [])
            
            # Sempre salvar os dados retornados da API (mesmo se vazio)
            instance.dados_prodam = dados_prodam
            instance.save(update_fields=['dados_prodam'])
            
            if not dados_prodam:
                logger.warning('API PRODAM retornou lista vazia')
                instance.status = 'CONCLUIDO'
                instance.save()
                serializer_response = ImportacaoEscolhasListSerializer(instance)
                return Response(serializer_response.data, status=status.HTTP_201_CREATED)
            
            # 5. Transformar e enviar para MS-Escolhas
            logger.info(f'Enviando {len(dados_prodam)} registros para MS-Escolhas')
            api_escolhas_service = ApiEscolhasService(
                base_url=settings.ESCOLHA_API_URL,
                timeout_seconds=settings.ESCOLHA_API_TIMEOUT
            )
            
            api_escolhas_service.enviar_escolhas_prodam(
                processo_uuid=processo_uuid,
                concurso_uuid=concurso_uuid,
                dados_prodam=dados_prodam,
                importacao_obj=instance
            )
            
            # 6. Atualizar status e quantidade de registros
            instance.status = 'CONCLUIDO'
            instance.save()
            
            logger.info(f'Importação concluída com sucesso: {len(dados_prodam)} registros')
            
        except Exception as exc:
            logger.error(f'Erro durante importação de escolhas: {exc}', exc_info=True)
            instance.status = 'ERRO'
            instance.save()
            
            try:
                registrar_erro(
                    instance,
                    mensagem='Erro durante importação de escolhas',
                    detalhes=str(exc),
                    exc=exc
                )
            except Exception:
                pass
            
            return Response(
                {'detail': f'Erro ao processar importação: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 7. Retornar resposta
        instance.refresh_from_db()
        serializer_response = ImportacaoEscolhasListSerializer(instance)
        headers = self.get_success_headers(serializer_response.data)
        return Response(serializer_response.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'], url_path='erros')
    def listar_erros(self, request):
        """Lista erros de importação de escolhas."""
        importacao_uuid = request.query_params.get('importacao_uuid', None)
        qs = queryset_erros_por_modelo(ImportacaoEscolhas, importacao_uuid=importacao_uuid).select_related('content_type')
        serializer = ImportacaoErrosListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='erros/download')
    def download_erros(self, request):
        """Download dos erros de importação de escolhas em formato texto."""
        importacao_uuid = request.query_params.get('importacao_uuid', None)
        qs = queryset_erros_por_modelo(ImportacaoEscolhas, importacao_uuid=importacao_uuid).select_related('content_type')
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
        resp['Content-Disposition'] = f'attachment; filename="escolhas_erros_{agora}.txt"'
        return resp


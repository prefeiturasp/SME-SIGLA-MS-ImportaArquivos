from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
import logging
from django.conf import settings

from ..models import ImportacaoEscolhas
from ..serializers import (
    ImportacaoEscolhasCreateSerializer,
    ImportacaoEscolhasListSerializer,
    EscolhasImportacaoSerializer,
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
            instance.dados_prodam = dados_prodam
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


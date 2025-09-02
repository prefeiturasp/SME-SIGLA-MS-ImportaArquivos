"""
Serviços para gerenciamento de importações de arquivos.
"""
from django.db import transaction
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import ImportacaoArquivos
import os
import logging

logger = logging.getLogger(__name__)


class ImportacaoArquivosService:
    """
    Serviço para operações com ImportacaoArquivos.
    """
    
    @staticmethod
    def criar_importacao(nome, arquivo, descricao=None, status='pendente'):
        """
        Cria uma nova importação de arquivo.
        
        Args:
            nome (str): Nome da importação
            arquivo (File): Arquivo a ser importado
            descricao (str, optional): Descrição da importação
            status (str, optional): Status inicial da importação
            
        Returns:
            ImportacaoArquivos: Instância criada
        """
        try:
            with transaction.atomic():
                importacao = ImportacaoArquivos.objects.create(
                    nome=nome,
                    descricao=descricao,
                    arquivo=arquivo,
                    status=status
                )
                logger.info(f'Importação criada: {importacao.uuid} - {importacao.nome}')
                return importacao
        except Exception as e:
            logger.error(f'Erro ao criar importação: {str(e)}')
            raise
    
    @staticmethod
    def atualizar_status(importacao_uuid, novo_status):
        """
        Atualiza o status de uma importação.
        
        Args:
            importacao_uuid (UUID): UUID da importação
            novo_status (str): Novo status
            
        Returns:
            ImportacaoArquivos: Instância atualizada
        """
        try:
            importacao = ImportacaoArquivos.objects.get(uuid=importacao_uuid)
            status_anterior = importacao.status
            importacao.status = novo_status
            importacao.save(update_fields=['status', 'atualizado_em'])
            
            logger.info(
                f'Status atualizado para importação {importacao_uuid}: '
                f'{status_anterior} -> {novo_status}'
            )
            return importacao
        except ImportacaoArquivos.DoesNotExist:
            logger.error(f'Importação não encontrada: {importacao_uuid}')
            raise
        except Exception as e:
            logger.error(f'Erro ao atualizar status: {str(e)}')
            raise
    
    @staticmethod
    def listar_por_status(status):
        """
        Lista importações por status.
        
        Args:
            status (str): Status a filtrar
            
        Returns:
            QuerySet: Queryset das importações
        """
        return ImportacaoArquivos.objects.filter(status=status).order_by('-criado_em')
    
    @staticmethod
    def remover_importacao(importacao_uuid, remover_arquivo=False):
        """
        Remove uma importação.
        
        Args:
            importacao_uuid (UUID): UUID da importação
            remover_arquivo (bool): Se deve remover o arquivo físico
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            with transaction.atomic():
                importacao = ImportacaoArquivos.objects.get(uuid=importacao_uuid)
                arquivo_path = None
                
                if remover_arquivo and importacao.arquivo:
                    arquivo_path = importacao.arquivo.path
                
                importacao.delete()
                
                # Remover arquivo físico se solicitado
                if remover_arquivo and arquivo_path and os.path.exists(arquivo_path):
                    try:
                        os.remove(arquivo_path)
                        logger.info(f'Arquivo físico removido: {arquivo_path}')
                    except Exception as e:
                        logger.warning(f'Erro ao remover arquivo físico: {str(e)}')
                
                logger.info(f'Importação removida: {importacao_uuid}')
                return True
                
        except ImportacaoArquivos.DoesNotExist:
            logger.error(f'Importação não encontrada: {importacao_uuid}')
            raise
        except Exception as e:
            logger.error(f'Erro ao remover importação: {str(e)}')
            raise
    
    @staticmethod
    def gerar_arquivo_exemplo(nome_arquivo="exemplo.csv"):
        """
        Gera um arquivo de exemplo para testes.
        
        Args:
            nome_arquivo (str): Nome do arquivo
            
        Returns:
            SimpleUploadedFile: Arquivo de exemplo
        """
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        conteudo = [
            'id,nome,email,departamento,data_cadastro',
            f'1,João Silva,joao@exemplo.com,TI,{timezone.now().date()}',
            f'2,Maria Santos,maria@exemplo.com,RH,{timezone.now().date()}',
            f'3,Pedro Costa,pedro@exemplo.com,Financeiro,{timezone.now().date()}',
        ]
        
        arquivo = SimpleUploadedFile(
            f"{timestamp}_{nome_arquivo}",
            '\n'.join(conteudo).encode('utf-8'),
            content_type='text/csv'
        )
        
        return arquivo
    
    @staticmethod
    def obter_estatisticas():
        """
        Obtém estatísticas das importações.
        
        Returns:
            dict: Estatísticas das importações
        """
        total = ImportacaoArquivos.objects.count()
        stats = {
            'total': total,
            'pendente': ImportacaoArquivos.objects.filter(status='pendente').count(),
            'processando': ImportacaoArquivos.objects.filter(status='processando').count(),
            'concluido': ImportacaoArquivos.objects.filter(status='concluido').count(),
            'erro': ImportacaoArquivos.objects.filter(status='erro').count(),
        }
        
        return stats

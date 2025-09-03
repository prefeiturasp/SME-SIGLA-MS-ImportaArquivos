"""
Django management command to clear import files data.
Comando Django para limpar dados de importação de arquivos.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from importa_arquivos.models import ImportacaoArquivos
import os


class Command(BaseCommand):
    help = 'Remove todos os registros da tabela de importações de arquivos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a exclusão sem solicitar confirmação interativa'
        )
        parser.add_argument(
            '--delete-files',
            action='store_true',
            help='Remove também os arquivos físicos do sistema'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['pendente', 'processando', 'concluido', 'erro'],
            help='Remove apenas importações com status específico'
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        delete_files = options['delete_files']
        status_filter = options['status']
        
        # Construir queryset baseado nos filtros
        queryset = ImportacaoArquivos.objects.all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        total_registros = queryset.count()
        
        if total_registros == 0:
            self.stdout.write(
                self.style.WARNING('Nenhum registro encontrado para remoção.')
            )
            return
        
        # Mensagem sobre o que será removido
        filter_msg = f" com status '{status_filter}'" if status_filter else ""
        self.stdout.write(
            self.style.WARNING(f'Serão removidos {total_registros} registros{filter_msg}.')
        )
        
        if delete_files:
            self.stdout.write(
                self.style.WARNING('⚠️  Os arquivos físicos também serão removidos!')
            )
        
        # Confirmação interativa se não foi passado --confirm
        if not confirm:
            resposta = input('Tem certeza que deseja continuar? (sim/não): ')
            if resposta.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write(self.style.WARNING('Operação cancelada.'))
                return
        
        try:
            with transaction.atomic():
                # Coletar informações dos arquivos antes de deletar, se necessário
                arquivos_para_deletar = []
                if delete_files:
                    for importacao in queryset:
                        if importacao.arquivo and hasattr(importacao.arquivo, 'path'):
                            arquivos_para_deletar.append(importacao.arquivo.path)
                
                # Executar a exclusão dos registros
                self.stdout.write(
                    self.style.SUCCESS(f'Removendo {total_registros} registros...')
                )
                
                deleted_count, _ = queryset.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {deleted_count} registros removidos com sucesso!')
                )
                
                # Remover arquivos físicos se solicitado
                if delete_files and arquivos_para_deletar:
                    arquivos_removidos = 0
                    arquivos_com_erro = 0
                    
                    for arquivo_path in arquivos_para_deletar:
                        try:
                            if os.path.exists(arquivo_path):
                                os.remove(arquivo_path)
                                arquivos_removidos += 1
                        except Exception as e:
                            arquivos_com_erro += 1
                            self.stdout.write(
                                self.style.WARNING(f'Erro ao remover arquivo {arquivo_path}: {e}')
                            )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'🗑️  {arquivos_removidos} arquivos físicos removidos.')
                    )
                    if arquivos_com_erro > 0:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  {arquivos_com_erro} arquivos não puderam ser removidos.')
                        )
                
                # Verificar resultado final
                registros_restantes = ImportacaoArquivos.objects.count()
                status_final = ""
                if status_filter:
                    registros_status = ImportacaoArquivos.objects.filter(status=status_filter).count()
                    status_final = f" (status '{status_filter}': {registros_status})"
                
                self.stdout.write(
                    self.style.SUCCESS(f'📊 Registros restantes na base: {registros_restantes}{status_final}')
                )
                
                if not status_filter and registros_restantes == 0:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Tabela completamente limpa!')
                    )
                
        except Exception as e:
            raise CommandError(f'Erro ao remover registros: {str(e)}') 
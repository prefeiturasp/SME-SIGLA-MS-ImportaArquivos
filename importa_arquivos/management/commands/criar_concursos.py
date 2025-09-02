"""
Django management command to create sample importacao arquivos.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from importa_arquivos.models import ImportacaoArquivos
from importa_arquivos.services import ImportacaoArquivosService
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
import random
import os


class Command(BaseCommand):
    help = 'Cria importações de arquivos de exemplo para desenvolvimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Número de importações de arquivos a serem criadas (padrão: 5)'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['pendente', 'processando', 'concluido', 'erro'],
            default='pendente',
            help='Status das importações criadas (padrão: pendente)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove todas as importações existentes antes de criar novas'
        )

    def handle(self, *args, **options):
        count = options['count']
        status = options['status']
        clean = options['clean']
        
        # Validações
        if count <= 0:
            raise CommandError('O número de importações deve ser maior que zero')
        
        if count > 100:
            self.stdout.write(
                self.style.WARNING(f'Criando {count} registros pode ser demorado...')
            )
        
        try:
            with transaction.atomic():
                # Limpar dados existentes se solicitado
                if clean:
                    total_existentes = ImportacaoArquivos.objects.count()
                    if total_existentes > 0:
                        self.stdout.write(
                            self.style.WARNING(f'Removendo {total_existentes} importações existentes...')
                        )
                        ImportacaoArquivos.objects.all().delete()
                        self.stdout.write(self.style.SUCCESS('✅ Dados limpos!'))
                
                self.stdout.write(
                    self.style.SUCCESS(f'Criando {count} importações de arquivos...')
                )
                
                importacoes_criadas = []
                
                # Criar importações em lote para melhor performance
                importacoes_para_criar = []
                
                for i in range(count):
                    # Criar arquivo de exemplo com conteúdo mais realista
                    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                    arquivo_content = self._generate_sample_csv(i+1)
                    arquivo = SimpleUploadedFile(
                        f"teste_{timestamp}_{i+1}.csv",
                        arquivo_content.encode('utf-8'),
                        content_type="text/csv"
                    )
                    
                    # Criar importação de arquivo com nome único
                    nome_importacao = f'Importação de Teste {i+1} - {timestamp}'
                    descricao = f'Arquivo de teste gerado automaticamente em {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'
                    
                    importacao = ImportacaoArquivos(
                        nome=nome_importacao,
                        descricao=descricao,
                        arquivo=arquivo,
                        status=status
                    )
                    
                    # Salvar individualmente devido ao FileField
                    importacao.save()
                    importacoes_criadas.append(importacao)
                    
                    if (i + 1) % 10 == 0:  # Progress feedback a cada 10 items
                        self.stdout.write(f'  ✓ Criadas {i + 1}/{count} importações...')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ {len(importacoes_criadas)} importações de arquivos criadas com sucesso!'
                    )
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'📁 Arquivos criados com status: {status}')
                )
                
                # Mostrar estatísticas finais
                total_registros = ImportacaoArquivos.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f'📊 Total de registros na base: {total_registros}')
                )
                
        except Exception as e:
            raise CommandError(f'Erro ao criar importações: {str(e)}')
    
    def _generate_sample_csv(self, index):
        """Gera conteúdo CSV de exemplo mais realista"""
        lines = [
            'id,nome,email,departamento,data_cadastro',
            f'{index},Usuario {index},usuario{index}@exemplo.com,TI,{timezone.now().date()}',
            f'{index+100},Usuario {index+100},usuario{index+100}@exemplo.com,RH,{timezone.now().date()}',
            f'{index+200},Usuario {index+200},usuario{index+200}@exemplo.com,Financeiro,{timezone.now().date()}',
        ]
        return '\n'.join(lines) 
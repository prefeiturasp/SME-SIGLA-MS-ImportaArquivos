"""
Django management command to create sample importacao arquivos.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from importa_arquivos.models import ImportacaoArquivos
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
import random


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

    def handle(self, *args, **options):
        count = options['count']
        status = options['status']
        
        self.stdout.write(
            self.style.SUCCESS(f'Criando {count} importações de arquivos...')
        )
        
        importacoes_criadas = []
        
        for i in range(count):
            # Criar arquivo de exemplo
            arquivo = SimpleUploadedFile(
                f"exemplo_{i+1}.csv",
                f"dados,exemplo,{i+1}\nlinha1,valor1,{i+1}\nlinha2,valor2,{i+1}".encode(),
                content_type="text/csv"
            )
            
            # Criar importação de arquivo com nome único
            nome_importacao = f'Importação de Exemplo {i+1}'
            descricao = f'Descrição da importação de exemplo {i+1}'
            
            importacao = ImportacaoArquivos.objects.create(
                nome=nome_importacao,
                descricao=descricao,
                arquivo=arquivo,
                status=status
            )
            
            self.stdout.write(
                f'  ✓ Criada importação: {importacao.nome} (Status: {importacao.status})'
            )
            
            importacoes_criadas.append(importacao)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {len(importacoes_criadas)} importações de arquivos criadas com sucesso!'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'📁 Arquivos criados com status: {status}'
            )
        ) 
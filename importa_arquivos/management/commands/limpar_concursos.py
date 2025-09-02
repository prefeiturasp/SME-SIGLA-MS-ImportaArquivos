"""
Django management command to clear all importacao arquivos.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from importa_arquivos.models import ImportacaoArquivos


class Command(BaseCommand):
    help = 'Remove todos os registros da tabela de importações de arquivos'

    def handle(self, *args, **options):

        # Contar registros existentes
        total_registros = ImportacaoArquivos.objects.count()
        # Executar a exclusão
        self.stdout.write(
            self.style.SUCCESS(f'Removendo {total_registros} registros...')
        )
        
        try:
            # Método 1: Usando delete() em queryset (mais seguro)
            ImportacaoArquivos.objects.all().delete()
            
            # Método 2: Usando SQL direto (mais rápido, mas menos seguro)
            # with connection.cursor() as cursor:
            #     cursor.execute("DELETE FROM importacao_arquivos")
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ {total_registros} registros removidos com sucesso!')
            )
            
            # Verificar se realmente foi limpo
            registros_restantes = ImportacaoArquivos.objects.count()
            if registros_restantes == 0:
                self.stdout.write(
                    self.style.SUCCESS('✅ Tabela completamente limpa!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Ainda restam {registros_restantes} registros.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao remover registros: {e}')
            ) 
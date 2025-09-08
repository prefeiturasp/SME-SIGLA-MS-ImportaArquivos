"""
Django management command to load initial layout data from JSON file.
Comando Django para carregar dados iniciais de layout de um arquivo JSON.
"""
import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from importa_arquivos.models import Layout
from django.utils.dateparse import parse_datetime
import uuid


class Command(BaseCommand):
    help = 'Carrega layouts iniciais de um arquivo JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/layouts_iniciais.json',
            help='Caminho para o arquivo JSON com os layouts (padrão: data/layouts_iniciais.json)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove todos os layouts existentes antes de carregar os novos'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a atualização de layouts existentes (baseado no UUID)'
        )

    def handle(self, *args, **options):
        arquivo_json = options['file']
        clean = options['clean']
        force = options['force']
        
        # Verificar se o arquivo existe
        if not os.path.exists(arquivo_json):
            raise CommandError(f'Arquivo não encontrado: {arquivo_json}')
        
        self.stdout.write(f'📁 Carregando layouts de: {arquivo_json}')
        
        try:
            # Ler e validar JSON
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                layouts_data = json.load(f)
            
            if not isinstance(layouts_data, list):
                raise CommandError('O arquivo JSON deve conter uma lista de layouts')
            
            self.stdout.write(f'📊 Encontrados {len(layouts_data)} layouts para carregar')
            
            # Limpar layouts existentes se solicitado
            if clean:
                self.stdout.write(
                    self.style.WARNING('🧹 Removendo todos os layouts existentes...')
                )
                Layout.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS('✅ Layouts existentes removidos')
                )
            
            # Carregar layouts em uma transação
            with transaction.atomic():
                layouts_criados = 0
                layouts_atualizados = 0
                layouts_ignorados = 0
                
                for i, layout_data in enumerate(layouts_data, 1):
                    resultado = self._processar_layout(layout_data, force, i)
                    
                    if resultado == 'criado':
                        layouts_criados += 1
                    elif resultado == 'atualizado':
                        layouts_atualizados += 1
                    else:
                        layouts_ignorados += 1
                
                # Relatório final
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ Carga concluída com sucesso!')
                )
                self.stdout.write(f'   📈 Layouts criados: {layouts_criados}')
                self.stdout.write(f'   🔄 Layouts atualizados: {layouts_atualizados}')
                self.stdout.write(f'   ⏭️  Layouts ignorados: {layouts_ignorados}')
                
                # Mostrar estatísticas finais
                total_layouts = Layout.objects.count()
                self.stdout.write(f'   📊 Total de layouts na base: {total_layouts}')
                
        except json.JSONDecodeError as e:
            raise CommandError(f'Erro ao ler JSON: {e}')
        except Exception as e:
            raise CommandError(f'Erro durante a carga: {e}')

    def _processar_layout(self, layout_data, force, index):
        """
        Processa um layout individual e retorna o resultado da operação.
        
        Returns:
            str: 'criado', 'atualizado' ou 'ignorado'
        """
        try:
            # Validar campos obrigatórios
            required_fields = ['uuid', 'tipo_de_layout', 'dados']
            for field in required_fields:
                if field not in layout_data:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Layout {index}: Campo obrigatório "{field}" não encontrado')
                    )
                    return 'ignorado'
            
            layout_uuid = layout_data['uuid']
            tipo_layout = layout_data['tipo_de_layout']
            dados = layout_data['dados']
            
            # Validar UUID
            try:
                uuid_obj = uuid.UUID(layout_uuid)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'❌ Layout {index}: UUID inválido: {layout_uuid}')
                )
                return 'ignorado'
            
            # Validar dados (deve ser uma lista)
            if not isinstance(dados, list):
                self.stdout.write(
                    self.style.ERROR(f'❌ Layout {index}: Campo "dados" deve ser uma lista')
                )
                return 'ignorado'
            
            # Verificar se layout já existe
            layout_existente = Layout.objects.filter(uuid=layout_uuid).first()
            
            if layout_existente:
                if force:
                    # Atualizar layout existente
                    layout_existente.tipo_de_layout = tipo_layout
                    layout_existente.dados = dados
                    layout_existente.save()
                    
                    self.stdout.write(f'🔄 Layout {index} atualizado: {tipo_layout} (UUID: {layout_uuid})')
                    return 'atualizado'
                else:
                    self.stdout.write(f'⏭️  Layout {index} já existe: {tipo_layout} (UUID: {layout_uuid}) - use --force para atualizar')
                    return 'ignorado'
            else:
                # Criar novo layout
                criado_em = layout_data.get('criado_em')
                if criado_em:
                    try:
                        criado_em = parse_datetime(criado_em)
                    except:
                        criado_em = timezone.now()
                else:
                    criado_em = timezone.now()
                
                layout = Layout(
                    uuid=layout_uuid,
                    tipo_de_layout=tipo_layout,
                    dados=dados,
                    criado_em=criado_em
                )
                layout.save()
                
                self.stdout.write(f'✅ Layout {index} criado: {tipo_layout} ({len(dados)} campos)')
                return 'criado'
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao processar layout {index}: {e}')
            )
            return 'ignorado'

    def _validar_dados_layout(self, dados):
        """
        Valida a estrutura dos dados do layout.
        """
        for i, campo in enumerate(dados):
            if not isinstance(campo, dict):
                raise ValueError(f"Campo {i+1} deve ser um objeto")
            
            required_fields = ['ordem', 'campo', 'tipo', 'tamanho', 'regras_de_validacao']
            for field in required_fields:
                if field not in campo:
                    raise ValueError(f"Campo obrigatório '{field}' não encontrado no campo {i+1}")

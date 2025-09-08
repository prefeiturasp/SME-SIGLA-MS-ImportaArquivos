"""
Django management command to manage layouts stored in JSON file.
Comando Django para gerenciar layouts armazenados em arquivo JSON.
"""
import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from importa_arquivos.layout_service import LayoutService


class Command(BaseCommand):
    help = 'Gerencia layouts armazenados em arquivo JSON'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Ações disponíveis')
        
        # Comando: carregar
        carregar_parser = subparsers.add_parser('carregar', help='Carrega layouts de um arquivo JSON')
        carregar_parser.add_argument(
            '--file',
            type=str,
            default='data/layouts.json',
            help='Caminho para o arquivo JSON com os layouts (padrão: data/layouts.json)'
        )
        carregar_parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove todos os layouts existentes antes de carregar os novos'
        )
        carregar_parser.add_argument(
            '--force',
            action='store_true',
            help='Força a atualização de layouts existentes (baseado no UUID)'
        )
        
        # Comando: listar
        listar_parser = subparsers.add_parser('listar', help='Lista todos os layouts')
        listar_parser.add_argument(
            '--formato',
            choices=['table', 'json'],
            default='table',
            help='Formato de saída (padrão: table)'
        )
        
        # Comando: backup
        backup_parser = subparsers.add_parser('backup', help='Cria backup dos layouts')
        backup_parser.add_argument(
            '--output',
            type=str,
            help='Caminho para o arquivo de backup (padrão: auto-gerado)'
        )
        
        # Comando: restaurar
        restaurar_parser = subparsers.add_parser('restaurar', help='Restaura layouts de um backup')
        restaurar_parser.add_argument(
            'backup_file',
            type=str,
            help='Caminho para o arquivo de backup'
        )
        
        # Comando: remover
        remover_parser = subparsers.add_parser('remover', help='Remove um layout por UUID')
        remover_parser.add_argument(
            'uuid',
            type=str,
            help='UUID do layout a ser removido'
        )
        
        # Comando: exportar
        exportar_parser = subparsers.add_parser('exportar', help='Exporta layouts para arquivo')
        exportar_parser.add_argument(
            '--output',
            type=str,
            required=True,
            help='Caminho para o arquivo de exportação'
        )
        exportar_parser.add_argument(
            '--tipo',
            type=str,
            help='Filtrar por tipo de layout específico'
        )

    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.stdout.write(
                self.style.ERROR('Ação não especificada. Use --help para ver opções disponíveis.')
            )
            return
        
        try:
            if action == 'carregar':
                self.carregar_layouts(options)
            elif action == 'listar':
                self.listar_layouts(options)
            elif action == 'backup':
                self.criar_backup(options)
            elif action == 'restaurar':
                self.restaurar_backup(options)
            elif action == 'remover':
                self.remover_layout(options)
            elif action == 'exportar':
                self.exportar_layouts(options)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Ação "{action}" não reconhecida.')
                )
        except Exception as e:
            raise CommandError(f'Erro durante execução: {e}')

    def carregar_layouts(self, options):
        """Carrega layouts de um arquivo JSON."""
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
                backup_path = LayoutService.backup_layouts()
                self.stdout.write(f'💾 Backup criado em: {backup_path}')
                LayoutService._save_layouts([])  # Limpar arquivo
                self.stdout.write(
                    self.style.SUCCESS('✅ Layouts existentes removidos')
                )
            
            # Carregar layouts
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
            total_layouts = len(LayoutService.list_layouts())
            self.stdout.write(f'   📊 Total de layouts: {total_layouts}')
            
        except json.JSONDecodeError as e:
            raise CommandError(f'Erro ao ler JSON: {e}')

    def _processar_layout(self, layout_data, force, index):
        """Processa um layout individual."""
        try:
            layout_uuid = layout_data.get('uuid')
            tipo_layout = layout_data.get('tipo_de_layout')
            
            if not layout_uuid or not tipo_layout:
                self.stdout.write(
                    self.style.ERROR(f'❌ Layout {index}: UUID ou tipo_de_layout não encontrado')
                )
                return 'ignorado'
            
            # Verificar se layout já existe
            layout_existente = LayoutService.get_layout_by_uuid(layout_uuid)
            
            if layout_existente:
                if force:
                    # Atualizar layout existente
                    LayoutService.update_layout(layout_uuid, layout_data)
                    self.stdout.write(f'🔄 Layout {index} atualizado: {tipo_layout} (UUID: {layout_uuid})')
                    return 'atualizado'
                else:
                    self.stdout.write(f'⏭️  Layout {index} já existe: {tipo_layout} (UUID: {layout_uuid}) - use --force para atualizar')
                    return 'ignorado'
            else:
                # Criar novo layout
                LayoutService.create_layout(layout_data)
                total_campos = len(layout_data.get('dados', []))
                self.stdout.write(f'✅ Layout {index} criado: {tipo_layout} ({total_campos} campos)')
                return 'criado'
                
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao processar layout {index}: {e}')
            )
            return 'ignorado'
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro inesperado no layout {index}: {e}')
            )
            return 'ignorado'

    def listar_layouts(self, options):
        """Lista todos os layouts."""
        formato = options['formato']
        
        try:
            layouts = LayoutService.list_layouts()
            
            if not layouts:
                self.stdout.write('📝 Nenhum layout encontrado.')
                return
            
            if formato == 'json':
                self.stdout.write(json.dumps(layouts, indent=2, ensure_ascii=False))
            else:
                self.stdout.write(f'📋 Total de layouts: {len(layouts)}\n')
                
                for layout in layouts:
                    uuid_layout = layout.get('uuid', 'N/A')
                    tipo = layout.get('tipo_de_layout', 'N/A')
                    total_campos = len(layout.get('dados', []))
                    criado_em = layout.get('criado_em', 'N/A')
                    
                    self.stdout.write(f'🔹 {tipo}')
                    self.stdout.write(f'   UUID: {uuid_layout}')
                    self.stdout.write(f'   Campos: {total_campos}')
                    self.stdout.write(f'   Criado: {criado_em}')
                    self.stdout.write('')
                    
        except Exception as e:
            raise CommandError(f'Erro ao listar layouts: {e}')

    def criar_backup(self, options):
        """Cria backup dos layouts."""
        output_path = options.get('output')
        
        try:
            backup_path = LayoutService.backup_layouts(output_path)
            self.stdout.write(
                self.style.SUCCESS(f'💾 Backup criado com sucesso: {backup_path}')
            )
            
            # Mostrar estatísticas
            layouts = LayoutService.list_layouts()
            self.stdout.write(f'📊 {len(layouts)} layouts salvos no backup')
            
        except Exception as e:
            raise CommandError(f'Erro ao criar backup: {e}')

    def restaurar_backup(self, options):
        """Restaura layouts de um backup."""
        backup_file = options['backup_file']
        
        try:
            # Criar backup atual antes de restaurar
            backup_atual = LayoutService.backup_layouts()
            self.stdout.write(f'💾 Backup atual criado em: {backup_atual}')
            
            # Restaurar
            count = LayoutService.restore_layouts(backup_file)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ {count} layouts restaurados de: {backup_file}')
            )
            
        except Exception as e:
            raise CommandError(f'Erro ao restaurar backup: {e}')

    def remover_layout(self, options):
        """Remove um layout por UUID."""
        layout_uuid = options['uuid']
        
        try:
            # Verificar se layout existe
            layout = LayoutService.get_layout_by_uuid(layout_uuid)
            if not layout:
                self.stdout.write(
                    self.style.ERROR(f'❌ Layout com UUID {layout_uuid} não encontrado')
                )
                return
            
            tipo_layout = layout.get('tipo_de_layout', 'N/A')
            
            # Confirmar remoção
            self.stdout.write(f'⚠️  Você está prestes a remover o layout: {tipo_layout} (UUID: {layout_uuid})')
            
            if LayoutService.delete_layout(layout_uuid):
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Layout {tipo_layout} removido com sucesso')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Falha ao remover layout')
                )
                
        except Exception as e:
            raise CommandError(f'Erro ao remover layout: {e}')

    def exportar_layouts(self, options):
        """Exporta layouts para arquivo."""
        output_path = options['output']
        tipo_filter = options.get('tipo')
        
        try:
            layouts = LayoutService.list_layouts()
            
            # Aplicar filtro se especificado
            if tipo_filter:
                layouts = [l for l in layouts if l.get('tipo_de_layout') == tipo_filter]
                self.stdout.write(f'🔍 Filtrando por tipo: {tipo_filter}')
            
            if not layouts:
                self.stdout.write('📝 Nenhum layout encontrado para exportar.')
                return
            
            # Salvar arquivo
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(layouts, f, indent=4, ensure_ascii=False)
            
            self.stdout.write(
                self.style.SUCCESS(f'💾 {len(layouts)} layouts exportados para: {output_path}')
            )
            
        except Exception as e:
            raise CommandError(f'Erro ao exportar layouts: {e}')
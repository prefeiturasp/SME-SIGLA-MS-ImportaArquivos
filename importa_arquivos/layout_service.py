"""
Serviço para gerenciar layouts armazenados em arquivo JSON.
"""
import json
import os
import uuid as uuid_module
from datetime import datetime
from typing import List, Dict, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class LayoutService:
    """
    Serviço para gerenciar layouts armazenados em arquivo JSON.
    """
    
    LAYOUTS_FILE_PATH = os.path.join(settings.BASE_DIR, 'data', 'layouts.json')
    
    @classmethod
    def _ensure_data_directory(cls) -> None:
        """Garante que o diretório data existe."""
        data_dir = os.path.dirname(cls.LAYOUTS_FILE_PATH)
        os.makedirs(data_dir, exist_ok=True)
    
    @classmethod
    def _load_layouts(cls) -> List[Dict[str, Any]]:
        """
        Carrega todos os layouts do arquivo JSON.
        
        Returns:
            List[Dict]: Lista de layouts
        """
        try:
            if not os.path.exists(cls.LAYOUTS_FILE_PATH):
                cls._ensure_data_directory()
                cls._save_layouts([])  # Cria arquivo vazio
                return []
            
            with open(cls.LAYOUTS_FILE_PATH, 'r', encoding='utf-8') as f:
                layouts = json.load(f)
                return layouts if isinstance(layouts, list) else []
        except (json.JSONDecodeError, IOError) as e:
            raise ValidationError(f"Erro ao carregar layouts: {e}")
    
    @classmethod
    def _save_layouts(cls, layouts: List[Dict[str, Any]]) -> None:
        """
        Salva layouts no arquivo JSON.
        
        Args:
            layouts: Lista de layouts para salvar
        """
        try:
            cls._ensure_data_directory()
            with open(cls.LAYOUTS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(layouts, f, indent=4, ensure_ascii=False)
        except IOError as e:
            raise ValidationError(f"Erro ao salvar layouts: {e}")
    
    @classmethod
    def list_layouts(cls) -> List[Dict[str, Any]]:
        """
        Lista todos os layouts.
        
        Returns:
            List[Dict]: Lista de todos os layouts
        """
        return cls._load_layouts()
    
    @classmethod
    def get_layout_by_uuid(cls, layout_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Busca layout por UUID.
        
        Args:
            layout_uuid: UUID do layout
            
        Returns:
            Dict ou None: Layout encontrado ou None
        """
        layouts = cls._load_layouts()
        for layout in layouts:
            if layout.get('uuid') == layout_uuid:
                return layout
        return None
    
    @classmethod
    def get_layout_by_tipo(cls, tipo_layout: str) -> Optional[Dict[str, Any]]:
        """
        Busca layout por tipo.
        
        Args:
            tipo_layout: Tipo do layout
            
        Returns:
            Dict ou None: Layout encontrado ou None
        """
        layouts = cls._load_layouts()
        for layout in layouts:
            if layout.get('tipo_de_layout') == tipo_layout:
                return layout
        return None
    
    @classmethod
    def create_layout(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo layout.
        
        Args:
            data: Dados do layout
            
        Returns:
            Dict: Layout criado
            
        Raises:
            ValidationError: Se dados inválidos ou layout já existe
        """
        cls._validate_layout_data(data)
        
        layouts = cls._load_layouts()
        
        # Verificar se UUID já existe
        layout_uuid = data.get('uuid')
        if layout_uuid and cls.get_layout_by_uuid(layout_uuid):
            raise ValidationError(f"Layout com UUID {layout_uuid} já existe")
        
        # Verificar se tipo já existe
        tipo_layout = data.get('tipo_de_layout')
        if cls.get_layout_by_tipo(tipo_layout):
            raise ValidationError(f"Layout do tipo {tipo_layout} já existe")
        
        # Gerar UUID se não fornecido
        if not layout_uuid:
            data['uuid'] = str(uuid_module.uuid4())
        
        # Definir timestamp de criação
        if not data.get('criado_em'):
            data['criado_em'] = timezone.now().isoformat()
        
        # Calcular total de campos
        data['total_campos'] = len(data.get('dados', []))
        
        # Adicionar layout à lista
        layouts.append(data)
        cls._save_layouts(layouts)
        
        return data
    
    @classmethod
    def update_layout(cls, layout_uuid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza um layout existente.
        
        Args:
            layout_uuid: UUID do layout
            data: Novos dados do layout
            
        Returns:
            Dict: Layout atualizado
            
        Raises:
            ValidationError: Se layout não existe ou dados inválidos
        """
        cls._validate_layout_data(data)
        
        layouts = cls._load_layouts()
        layout_index = None
        
        # Encontrar o layout
        for i, layout in enumerate(layouts):
            if layout.get('uuid') == layout_uuid:
                layout_index = i
                break
        
        if layout_index is None:
            raise ValidationError(f"Layout com UUID {layout_uuid} não encontrado")
        
        # Verificar se novo tipo conflita com outros layouts
        novo_tipo = data.get('tipo_de_layout')
        if novo_tipo:
            for i, layout in enumerate(layouts):
                if i != layout_index and layout.get('tipo_de_layout') == novo_tipo:
                    raise ValidationError(f"Já existe outro layout do tipo {novo_tipo}")
        
        # Preservar UUID e data de criação
        data['uuid'] = layout_uuid
        if not data.get('criado_em'):
            data['criado_em'] = layouts[layout_index].get('criado_em', timezone.now().isoformat())
        
        # Calcular total de campos
        data['total_campos'] = len(data.get('dados', []))
        
        # Atualizar layout
        layouts[layout_index] = data
        cls._save_layouts(layouts)
        
        return data
    
    @classmethod
    def delete_layout(cls, layout_uuid: str) -> bool:
        """
        Remove um layout.
        
        Args:
            layout_uuid: UUID do layout
            
        Returns:
            bool: True se removido, False se não encontrado
        """
        layouts = cls._load_layouts()
        layout_index = None
        
        # Encontrar o layout
        for i, layout in enumerate(layouts):
            if layout.get('uuid') == layout_uuid:
                layout_index = i
                break
        
        if layout_index is None:
            return False
        
        # Remover layout
        layouts.pop(layout_index)
        cls._save_layouts(layouts)
        
        return True
    
    @classmethod
    def _validate_layout_data(cls, data: Dict[str, Any]) -> None:
        """
        Valida dados de layout.
        
        Args:
            data: Dados para validar
            
        Raises:
            ValidationError: Se dados inválidos
        """
        # Validar campos obrigatórios
        if not data.get('tipo_de_layout'):
            raise ValidationError("Campo 'tipo_de_layout' é obrigatório")
        
        dados = data.get('dados')
        if not isinstance(dados, list):
            raise ValidationError("Campo 'dados' deve ser uma lista")
        
        if not dados:
            raise ValidationError("Layout deve ter pelo menos um campo")
        
        # Validar cada campo
        ordens_usadas = set()
        for i, campo in enumerate(dados):
            if not isinstance(campo, dict):
                raise ValidationError(f"Campo {i+1}: deve ser um objeto")
            
            # Validar campos obrigatórios do campo
            required_fields = ['campo', 'tipo', 'ordem', 'tamanho', 'regras_de_validacao']
            for field in required_fields:
                if field not in campo:
                    raise ValidationError(f"Campo {i+1}: '{field}' é obrigatório")
            
            # Validar ordem única
            ordem = campo.get('ordem')
            if ordem in ordens_usadas:
                raise ValidationError(f"Campo {i+1}: ordem {ordem} já está sendo usada")
            ordens_usadas.add(ordem)
            
            # Validar tipos permitidos
            tipos_permitidos = ['string', 'integer', 'decimal', 'date', 'text']
            if campo.get('tipo') not in tipos_permitidos:
                raise ValidationError(f"Campo {i+1}: tipo deve ser um de {tipos_permitidos}")
            
            # Validar tamanho
            try:
                tamanho = int(campo.get('tamanho', 0))
                if tamanho <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError(f"Campo {i+1}: tamanho deve ser um número inteiro positivo")
    
    @classmethod
    def get_tipos_layout_disponiveis(cls) -> List[str]:
        """
        Retorna lista de tipos de layout disponíveis.
        
        Returns:
            List[str]: Lista de tipos
        """
        layouts = cls._load_layouts()
        return [layout.get('tipo_de_layout') for layout in layouts if layout.get('tipo_de_layout')]
    
    @classmethod
    def backup_layouts(cls, backup_path: Optional[str] = None) -> str:
        """
        Cria backup dos layouts.
        
        Args:
            backup_path: Caminho para o backup (opcional)
            
        Returns:
            str: Caminho do arquivo de backup criado
        """
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(settings.BASE_DIR, 'data', f'layouts_backup_{timestamp}.json')
        
        layouts = cls._load_layouts()
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(layouts, f, indent=4, ensure_ascii=False)
            return backup_path
        except IOError as e:
            raise ValidationError(f"Erro ao criar backup: {e}")
    
    @classmethod
    def restore_layouts(cls, backup_path: str) -> int:
        """
        Restaura layouts de um backup.
        
        Args:
            backup_path: Caminho do arquivo de backup
            
        Returns:
            int: Número de layouts restaurados
            
        Raises:
            ValidationError: Se arquivo inválido
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                layouts = json.load(f)
            
            if not isinstance(layouts, list):
                raise ValidationError("Arquivo de backup deve conter uma lista de layouts")
            
            # Validar cada layout
            for layout in layouts:
                cls._validate_layout_data(layout)
            
            cls._save_layouts(layouts)
            return len(layouts)
            
        except FileNotFoundError:
            raise ValidationError(f"Arquivo de backup não encontrado: {backup_path}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Arquivo de backup inválido: {e}")
        except IOError as e:
            raise ValidationError(f"Erro ao ler backup: {e}")

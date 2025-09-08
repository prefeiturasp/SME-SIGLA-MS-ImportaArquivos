import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog

from .constants import ImportacaoStatus, TipoLayout, FileValidationConstants
from .services import RobustServerIntegrationService, FileValidationService
  
class BaseModel(models.Model):
    """
    Model base com UUID, criado_em e atualizado_em.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        abstract = True


 


class ImportacaoArquivos(BaseModel):
    """
    Model para importação de arquivos.
    Implementa o protocol ImportacaoUpdater para integração com services.
    """
    
    history = AuditlogHistoryField()
    arquivo_nome_original = models.CharField(
        max_length=255, 
        default=FileValidationConstants.DEFAULT_FILENAME, 
        verbose_name="Nome do Arquivo Original"
    )
    arquivo_tamanho = models.PositiveIntegerField(default=0, verbose_name="Tamanho do Arquivo (bytes)")
    arquivo_content_type = models.CharField(
        max_length=100, 
        default=FileValidationConstants.CSV_CONTENT_TYPE, 
        verbose_name="Tipo do Arquivo"
    )
    
    # Campo temporário para validação (não salvo no banco)
    _arquivo_content = None
    
    tipo_de_layout = models.CharField(
        max_length=30,
        choices=TipoLayout.choices(),
        default=TipoLayout.VAGAS.value,
        verbose_name="Tipo de Layout",
        help_text="Tipo de layout que define a estrutura dos dados do arquivo"
    )
    
    # Novos campos
    concurso = models.CharField(max_length=255, verbose_name="Concurso", default="")
    cargo = models.CharField(max_length=255, verbose_name="Cargo", default="")
    
    # Status interno (não recebido via payload)
    status = models.CharField(
        max_length=20,
        choices=ImportacaoStatus.choices(),
        default=ImportacaoStatus.PENDENTE.value,
        verbose_name="Status"
    )
    
    # Services injetados
    _validation_service = None
    _integration_service = None

    class Meta:
        db_table = 'importacao_arquivos'
        verbose_name = "Importação de Arquivo"
        verbose_name_plural = "Importações de Arquivos"
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.concurso} - {self.cargo} ({self.arquivo_nome_original})"
    
    @property
    def validation_service(self) -> FileValidationService:
        """Lazy loading do serviço de validação."""
        if self._validation_service is None:
            self._validation_service = FileValidationService()
        return self._validation_service
    
    @property
    def integration_service(self) -> RobustServerIntegrationService:
        """Lazy loading do serviço de integração."""
        if self._integration_service is None:
            self._integration_service = RobustServerIntegrationService()
        return self._integration_service
    
    def set_arquivo_temporario(self, arquivo_uploaded) -> None:
        """
        Define o arquivo temporário para validação e envio (não salva no disco).
        
        Args:
            arquivo_uploaded: Arquivo enviado via upload
        """
        if not arquivo_uploaded:
            return
            
        self._arquivo_content = arquivo_uploaded.read()
        self.arquivo_nome_original = arquivo_uploaded.name
        self.arquivo_tamanho = len(self._arquivo_content)
        self.arquivo_content_type = arquivo_uploaded.content_type or FileValidationConstants.CSV_CONTENT_TYPE

    def clean(self) -> None:
        """Valida se o arquivo e o tipo de layout são correspondentes."""
        super().clean()
        if self._arquivo_content and self.tipo_de_layout:
            self._validate_file_against_layout()
    
    def update_status(self, new_status: ImportacaoStatus) -> None:
        """
        Atualiza o status da importação (implementa ImportacaoUpdater protocol).
        
        Args:
            new_status: Novo status para a importação
        """
        self.status = new_status.value
        super().save(update_fields=['status', 'atualizado_em'])

    def _validate_file_against_layout(self) -> None:
        """Valida arquivo contra layout usando o serviço de validação."""
        self.validation_service.validate_file_against_layout(
            self._arquivo_content, 
            self.tipo_de_layout
        )

    def save(self, *args, **kwargs) -> None:
        """
        Executa validação e tenta enviar para robust_server antes de salvar.
        Só salva no banco se a comunicação com o robust_server for bem-sucedida.
        """
        from .services import RobustServerCommunicationError
        
        self.clean()
        
        # Verificar se é um novo registro
        is_new_record = self._state.adding
        
        # Se é um novo registro com arquivo, tentar enviar primeiro para o robust_server
        if self._should_send_to_robust_server(is_new_record):
            try:
                # Definir um UUID temporário se ainda não foi salvo
                if not self.uuid:
                    import uuid
                    self.uuid = uuid.uuid4()
                
                # Definir criado_em temporariamente se não foi definido
                if not self.criado_em:
                    from django.utils import timezone
                    self.criado_em = timezone.now()
                
                # Tentar enviar para o robust server primeiro
                self._send_to_robust_server()
                
                # Se chegou aqui, a comunicação foi bem-sucedida, salvar no banco
                super().save(*args, **kwargs)
                
            except RobustServerCommunicationError as e:
                # Re-lançar a exceção para que seja tratada no serializer/view
                raise e
        else:
            # Para registros que não precisam ser enviados (updates, etc), salvar normalmente
            super().save(*args, **kwargs)
    
    def _should_send_to_robust_server(self, is_new_record: bool) -> bool:
        """
        Verifica se deve enviar arquivo para o robust server.
        
        Args:
            is_new_record: Se é um novo registro
            
        Returns:
            True se deve enviar, False caso contrário
        """
        return (
            is_new_record and 
            self.status == ImportacaoStatus.PENDENTE.value and 
            self._arquivo_content is not None
        )
    
    def _send_to_robust_server(self) -> None:
        """Envia arquivo para o robust server usando o serviço de integração."""
        self.integration_service.send_validated_file(self, self._arquivo_content)


class Layout(BaseModel):
    """
    Model para layouts de importação.
    """
    
    history = AuditlogHistoryField()
    tipo_de_layout = models.CharField(
        max_length=30,
        choices=TipoLayout.choices(),
        verbose_name="Tipo de Layout"
    )
    dados = models.JSONField(
        verbose_name="Dados do Layout",
        help_text="Lista de campos com estrutura: ordem, campo, tipo, tamanho, regras_de_validacao"
    )

    class Meta:
        db_table = 'layout'
        verbose_name = "Layout"
        verbose_name_plural = "Layouts"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Layout {self.tipo_de_layout} - {self.uuid}"

    def clean(self):
        """
        Valida a estrutura dos dados JSON.
        """
        super().clean()
        if self.dados:
            if not isinstance(self.dados, list):
                raise ValidationError("O campo 'dados' deve ser uma lista.")
            
            for item in self.dados:
                if not isinstance(item, dict):
                    raise ValidationError("Cada item em 'dados' deve ser um objeto.")
                
                required_fields = ['ordem', 'campo', 'tipo', 'tamanho', 'regras_de_validacao']
                for field in required_fields:
                    if field not in item:
                        raise ValidationError(f"Campo obrigatório '{field}' não encontrado no item: {item}")
                
                # Validar tipos específicos
                if not isinstance(item['ordem'], int):
                    raise ValidationError(f"Campo 'ordem' deve ser um número inteiro. Valor: {item['ordem']}")
                
                if not isinstance(item['campo'], str):
                    raise ValidationError(f"Campo 'campo' deve ser uma string. Valor: {item['campo']}")
                
                if not isinstance(item['tipo'], str):
                    raise ValidationError(f"Campo 'tipo' deve ser uma string. Valor: {item['tipo']}")
                
                if not isinstance(item['tamanho'], int):
                    raise ValidationError(f"Campo 'tamanho' deve ser um número inteiro. Valor: {item['tamanho']}")
                
                if not isinstance(item['regras_de_validacao'], str):
                    raise ValidationError(f"Campo 'regras_de_validacao' deve ser uma string. Valor: {item['regras_de_validacao']}")

    def save(self, *args, **kwargs):
        """
        Executa validação antes de salvar.
        """
        self.clean()
        super().save(*args, **kwargs)

    @property
    def total_campos(self):
        """
        Retorna o total de campos no layout.
        """
        return len(self.dados) if self.dados else 0

    def get_campo_por_ordem(self, ordem):
        """
        Retorna um campo específico pela sua ordem.
        """
        if not self.dados:
            return None
        
        for campo in self.dados:
            if campo.get('ordem') == ordem:
                return campo
        return None

    def get_campos_ordenados(self):
        """
        Retorna os campos ordenados pela ordem.
        """
        if not self.dados:
            return []
        
        return sorted(self.dados, key=lambda x: x.get('ordem', 0))


auditlog.register(ImportacaoArquivos)
auditlog.register(Layout)

import uuid
import json
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog


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
    """
    history = AuditlogHistoryField()
    nome = models.CharField(max_length=200, verbose_name="Nome do Arquivo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    arquivo = models.FileField(upload_to='importacoes/', verbose_name="Arquivo")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pendente', 'Pendente'),
            ('processando', 'Processando'),
            ('concluido', 'Concluído'),
            ('erro', 'Erro'),
        ],
        default='pendente',
        verbose_name="Status"
    )

    class Meta:
        db_table = 'importacao_arquivos'
        verbose_name = "Importação de Arquivo"
        verbose_name_plural = "Importações de Arquivos"
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome


class Layout(BaseModel):
    """
    Model para layouts de importação.
    """
    
    TIPO_LAYOUT_CHOICES = [
        ('VAGAS', 'Vagas'),
        ('CANDIDATOS_CLASSIFICADOS', 'Candidatos Classificados'),
    ]
    
    history = AuditlogHistoryField()
    tipo_de_layout = models.CharField(
        max_length=30,
        choices=TIPO_LAYOUT_CHOICES,
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

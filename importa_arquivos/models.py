import uuid
import json
import os
import requests
import base64
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from importa_arquivos.urls_externas import DOCUMENT_POST_IMPORTACAO_ARQUIVOS
  
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
    
    TIPO_LAYOUT_CHOICES = [
        ('VAGAS', 'Vagas'),
        ('CANDIDATOS_CLASSIFICADOS', 'Candidatos Classificados'),
    ]
    
    history = AuditlogHistoryField()
    nome = models.CharField(max_length=200, verbose_name="Nome do Arquivo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    arquivo = models.FileField(upload_to='importacoes/', verbose_name="Arquivo")
    tipo_de_layout = models.CharField(
        max_length=30,
        choices=TIPO_LAYOUT_CHOICES,
        default='VAGAS',
        verbose_name="Tipo de Layout",
        help_text="Tipo de layout que define a estrutura dos dados do arquivo"
    )
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

    def clean(self):
        """
        Valida se o arquivo e o tipo de layout são correspondentes.
        """
        super().clean()
        if self.arquivo and self.tipo_de_layout:
            self._validar_arquivo_tipo_layout()

    def _validar_arquivo_tipo_layout(self):
        """
        Valida se o arquivo está no formato correto para o tipo de layout.
        """
        import csv
        import io
        
        try:
            # Ler o arquivo e verificar os cabeçalhos
            arquivo_content = self.arquivo.read()
            self.arquivo.seek(0)  # Resetar o ponteiro do arquivo
            
            # Tentar diferentes encodings
            try:
                arquivo_text = arquivo_content.decode('utf-8-sig')  # Remove BOM automaticamente
            except UnicodeDecodeError:
                try:
                    arquivo_text = arquivo_content.decode('utf-8')
                except UnicodeDecodeError:
                    arquivo_text = arquivo_content.decode('latin-1')
            
            # Ler primeira linha (cabeçalhos)
            reader = csv.reader(io.StringIO(arquivo_text))
            headers = next(reader, [])
            
            # Obter o layout correspondente ao tipo
            try:
                layout = Layout.objects.get(tipo_de_layout=self.tipo_de_layout)
                campos_esperados = [campo['campo'] for campo in layout.get_campos_ordenados()]
                
                # Verificar se os cabeçalhos do arquivo correspondem aos campos do layout
                if not headers:
                    raise ValidationError(f"Arquivo CSV vazio ou sem cabeçalhos.")
                
                # Remover BOM e espaços em branco dos cabeçalhos
                headers_limpos = [h.strip().lstrip('\ufeff') for h in headers]
                
                # Verificar se todos os campos obrigatórios estão presentes
                campos_faltando = []
                for campo in campos_esperados:
                    if campo not in headers_limpos:
                        campos_faltando.append(campo)
                
                if campos_faltando:
                    raise ValidationError(
                        f"O arquivo não corresponde ao layout {self.tipo_de_layout}. "
                        f"Campos obrigatórios faltando: {', '.join(campos_faltando)}. "
                        f"Campos esperados: {', '.join(campos_esperados)}"
                    )
                
                # Verificar se há campos extras no arquivo
                campos_extras = []
                for header in headers_limpos:
                    if header not in campos_esperados:
                        campos_extras.append(header)
                
                if campos_extras:
                    raise ValidationError(
                        f"O arquivo contém campos não esperados para o layout {self.tipo_de_layout}: "
                        f"{', '.join(campos_extras)}. "
                        f"Campos permitidos: {', '.join(campos_esperados)}"
                    )
                        
            except Layout.DoesNotExist:
                raise ValidationError(f"Layout não encontrado para o tipo: {self.tipo_de_layout}")
                
        except UnicodeDecodeError:
            raise ValidationError("Arquivo deve estar em formato UTF-8.")
        except csv.Error as e:
            raise ValidationError(f"Erro ao processar arquivo CSV: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Erro ao validar arquivo: {str(e)}")

    def save(self, *args, **kwargs):
        """
        Executa validação antes de salvar e envia para o robust_server se validado.
        """
        self.clean()
        
        # Verificar se é um novo registro usando _state.adding
        is_new = self._state.adding
        
        # Salvar primeiro no banco local
        super().save(*args, **kwargs)
        
        # Se é um novo registro e está validado, enviar para o robust_server
        if is_new and self.status == 'pendente':
            self._enviar_para_robust_server()
    
    def _enviar_para_robust_server(self):
        """
        Envia os dados do arquivo validado para o robust_server via POST.
        """
        try:
            # URL do robust_server (configurável)
            
            endpoint = DOCUMENT_POST_IMPORTACAO_ARQUIVOS
            
            # Ler o arquivo e converter para base64
            self.arquivo.seek(0)
            arquivo_content = self.arquivo.read()
            arquivo_base64 = base64.b64encode(arquivo_content).decode('utf-8')
            
            # Preparar dados para envio
            payload = {
                'uuid': str(self.uuid),
                'nome': self.nome,
                'descricao': self.descricao,
                'tipo_de_layout': self.tipo_de_layout,
                'status': self.status,
                'arquivo': {
                    'name': os.path.basename(self.arquivo.name),
                    'content': arquivo_base64,
                    'content_type': 'text/csv'
                },
                'metadata': {
                    'criado_em': self.criado_em.isoformat(),
                    'fonte': 'SME-SIGLA-MS-ImportaArquivos'
                }
            }
            
            # Enviar via POST
            response = requests.post(
                endpoint,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'SME-SIGLA-ImportaArquivos/1.0'
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                # Atualizar status para indicar que foi enviado com sucesso
                self.status = 'processando'
                super().save(update_fields=['status', 'atualizado_em'])
                
        except Exception as e:
            # Log do erro, mas não falhar a operação principal
            pass


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

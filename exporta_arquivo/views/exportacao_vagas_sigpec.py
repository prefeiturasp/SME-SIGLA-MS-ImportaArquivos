"""ViewSet de exportação de vagas em formato SIGPEC.

- list: listagem (ou, se processo_uuid e cargo_uuid na query, retorna arquivo
.txt — compatibilidade).
- retrieve: detalhe de um registro.
- create: cria registro e executa a exportação (persiste processo_uuid,
cargo_uuid, concurso_*).
- download (detail): retorna arquivo .txt da exportação.
"""
from __future__ import annotations
from typing import Any
from django.http import HttpResponse
from ..models import ExportacaoVagasSigpec
from ..serializers import ExportacaoVagasSigpecCreateSerializer, ExportacaoVagasSigpecListSerializer
from ..services.exportacao_vagas_sigpec import buscar_vagas_escolas, formatar_arquivo_sigpec
from .base_exportacao import BaseExportacaoViewSet

class ExportacaoVagasSigpecViewSet(BaseExportacaoViewSet):
    """ViewSet para exportação de vagas SIGPEC."""
    queryset = ExportacaoVagasSigpec.objects.all()
    list_serializer_class = ExportacaoVagasSigpecListSerializer  # type: ignore[assignment]
    create_serializer_class = ExportacaoVagasSigpecCreateSerializer  # type: ignore[assignment]

    def gerar_arquivo(self, instance: Any) -> Any:
        """Gera resposta de arquivo .txt para os UUIDs dados.
        
        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        response = HttpResponse(instance.conteudo_arquivo.encode('utf-8'), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{instance.nome_arquivo}"'
        return response

    def executar_exportacao(self, instance: Any) -> None:
        """Executa a exportação SIGPEC, gera o arquivo e persiste conteúdo e nome.
        
        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        vagas_escolas = buscar_vagas_escolas(str(instance.processo_uuid), instance.cargo_codigo)
        conteudo = formatar_arquivo_sigpec(vagas_escolas)
        desc_safe = self.sanitizar_nome_arquivo(instance.processo_nome, max_len=60)
        cargo_safe = self.sanitizar_nome_arquivo(instance.cargo_nome, max_len=60)
        nome_arquivo = f'exportacao-vagas-sigpec-{cargo_safe}.{instance.cargo_codigo}.{desc_safe}.txt'
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.save(update_fields=['conteudo_arquivo', 'nome_arquivo'])

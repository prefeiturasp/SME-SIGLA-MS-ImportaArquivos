"""
ViewSet de exportação de candidatos por processo.

- list: listagem (ou, se processo_uuid e cargo_uuid na query, retorna arquivo .txt; concurso_uuid opcional).
- retrieve: detalhe de um registro.
- create: cria registro e executa a exportação (persiste processo_uuid, cargo_uuid, concurso_*).
- download (detail): retorna arquivo .txt da exportação.
"""
from django.http import HttpResponse

from ..models import ExportacaoCandidatosProcesso
from ..serializers import (
    ExportacaoCandidatosProcessoCreateSerializer,
    ExportacaoCandidatosProcessoListSerializer,
)
from ..services.exportacao_candidatos_processo import (
    exportar_candidatos_processo,
    formatar_arquivo_candidatos_processo,
)
from ..services.api_concursos import buscar_dados_concurso
from ..services.exceptions import (
    ExportacaoBadRequestException,
    ExportacaoNotFoundException,
    ExportacaoServiceUnavailableException,
)
from .base_exportacao import BaseExportacaoViewSet


class ExportacaoCandidatosProcessoViewSet(BaseExportacaoViewSet):
    """
    ViewSet para exportação de candidatos por processo.

    - list: lista registros (filtros, busca, ordenação, paginação).
    - create: cria o registro, executa a exportação e retorna o arquivo .txt para download.
    - retrieve: detalhe de um registro.
    - download (GET em /<uuid>/download/): retorna arquivo .txt para download.
    - GET list com processo_uuid e cargo_uuid (e opcionalmente concurso_uuid) na query: retorna arquivo .txt.
    """
    queryset = ExportacaoCandidatosProcesso.objects.all()
    list_serializer_class = ExportacaoCandidatosProcessoListSerializer
    create_serializer_class = ExportacaoCandidatosProcessoCreateSerializer

    def gerar_arquivo(self, instance):
        """Gera resposta de arquivo .txt a partir do registro (conteudo_arquivo e nome_arquivo)."""
        response = HttpResponse(
            instance.conteudo_arquivo.encode('utf-8'),
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = f'attachment; filename="{instance.nome_arquivo}"'
        return response

    def executar_exportacao(self, instance):
        """Executa a exportação de candidatos processo, gera o arquivo e persiste conteúdo e nome no registro."""
        concurso_uuid = str(instance.concurso_uuid) if instance.concurso_uuid else None
        processo_nome = getattr(instance, 'processo_nome', None) or None
        cargo_nome = getattr(instance, 'cargo_nome', None) or None
        cargo_codigo_payload = getattr(instance, 'cargo_codigo', None)
        concurso_codigo_payload = getattr(instance, 'concurso_codigo', None)
        concurso_data_criacao_payload = getattr(instance, 'concurso_data_criacao', None)

        # Se temos concurso_uuid mas ainda não temos código/data, buscar no MS-Concurso.
        if concurso_uuid and (concurso_codigo_payload is None or not (concurso_data_criacao_payload or "").strip()):
            codigo, data_criacao = buscar_dados_concurso(concurso_uuid)
            updates = []
            if concurso_codigo_payload is None and codigo is not None:
                instance.concurso_codigo = codigo
                concurso_codigo_payload = codigo
                updates.append("concurso_codigo")
            if (not (concurso_data_criacao_payload or "").strip()) and data_criacao:
                instance.concurso_data_criacao = data_criacao
                concurso_data_criacao_payload = data_criacao
                updates.append("concurso_data_criacao")
            if updates:
                instance.save(update_fields=updates)

        dados_concurso, lista_candidatos = exportar_candidatos_processo(
            str(instance.processo_uuid),
            str(instance.cargo_uuid),
            concurso_uuid=concurso_uuid,
            processo_nome=processo_nome,
            cargo_nome=cargo_nome,
            cargo_codigo=cargo_codigo_payload,
            concurso_codigo=concurso_codigo_payload,
            concurso_data_criacao=concurso_data_criacao_payload,
        )
        conteudo = formatar_arquivo_candidatos_processo(dados_concurso, lista_candidatos)
        cargo_nome_val = dados_concurso.get("cargo_nome") or "cargo"
        codigo_concurso = dados_concurso.get("codigo") or dados_concurso.get("cargo_codigo") or ""
        desc_safe = self.sanitizar_nome_arquivo(cargo_nome_val, max_len=60)
        nome_arquivo = f"candidatos_processo_{desc_safe}_{codigo_concurso}.txt"
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.save(update_fields=['conteudo_arquivo', 'nome_arquivo'])

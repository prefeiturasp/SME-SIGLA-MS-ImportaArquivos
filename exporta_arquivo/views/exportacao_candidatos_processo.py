"""
ViewSet de exportação de candidatos por processo.

- list: listagem (ou, se processo_uuid e cargo_uuid na query, retorna arquivo
.txt; concurso_uuid opcional).
- retrieve: detalhe de um registro.
- create: cria registro e executa a exportação (persiste processo_uuid,
cargo_uuid, concurso_*).
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
)
from .base_exportacao import BaseExportacaoViewSet


class ExportacaoCandidatosProcessoViewSet(BaseExportacaoViewSet):
    """
    ViewSet para exportação de candidatos por processo.

    - list: lista registros (filtros, busca, ordenação, paginação).
    - create: cria o registro, executa a exportação e retorna o arquivo .txt
    para download.
    - retrieve: detalhe de um registro.
    - download (GET em /<uuid>/download/): retorna arquivo .txt para download.
    - GET list com processo_uuid e cargo_uuid (e opcionalmente concurso_uuid)
    na query: retorna arquivo .txt.
    """

    queryset = ExportacaoCandidatosProcesso.objects.all()
    list_serializer_class = ExportacaoCandidatosProcessoListSerializer
    create_serializer_class = ExportacaoCandidatosProcessoCreateSerializer

    def gerar_arquivo(self, instance):
        """
        Gera resposta de arquivo .txt a partir do registro (conteudo_arquivo e
        nome_arquivo).
        """
        response = HttpResponse(
            instance.conteudo_arquivo.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{instance.nome_arquivo}"'
        )
        return response

    def executar_exportacao(self, instance):
        """
        Executa a exportação de candidatos processo, gera o arquivo e persiste
        conteúdo e nome no registro.
        """

        conteudo = exportar_candidatos_processo(instance)

        desc_safe = self.sanitizar_nome_arquivo(
            instance.cargo_nome, max_len=60
        )
        nome_arquivo = (
            f"candidatos_processo_{desc_safe}_{instance.concurso_codigo}.txt"
        )
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.save(update_fields=["conteudo_arquivo", "nome_arquivo"])

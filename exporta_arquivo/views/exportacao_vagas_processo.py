"""
ViewSet de exportação de vagas em formato vagas processo.

- list: listagem (ou, se processo_uuid e cargo_uuid na query, retorna arquivo
.txt — compatibilidade).
- retrieve: detalhe de um registro.
- create: cria registro e executa a exportação (persiste processo_uuid,
cargo_uuid, concurso_*).
- download (detail): retorna arquivo .txt da exportação.
"""

from django.http import HttpResponse

from ..models import ExportacaoVagasProcesso
from ..serializers import (
    ExportacaoVagasProcessoCreateSerializer,
    ExportacaoVagasProcessoListSerializer,
)
from ..services.exportacao_vagas_processo import (
    buscar_vagas_escolas,
    formatar_arquivo_vagas_processo,
)
from .base_exportacao import BaseExportacaoViewSet


class ExportacaoVagasProcessoViewSet(BaseExportacaoViewSet):
    """
    ViewSet para exportação de vagas processo.

    - list: lista registros (filtros, busca, ordenação, paginação).
    - create: cria o registro, executa a exportação e retorna o arquivo .txt
    para download.
    - retrieve: detalhe de um registro.
    - download (GET em /<uuid>/download/): retorna arquivo .txt para download.
    - GET list com processo_uuid e cargo_uuid na query: retorna arquivo .txt
    (comportamento legado).
    """

    queryset = ExportacaoVagasProcesso.objects.all()
    list_serializer_class = ExportacaoVagasProcessoListSerializer
    create_serializer_class = ExportacaoVagasProcessoCreateSerializer

    def gerar_arquivo(self, instance):
        """
        Gera resposta de arquivo .txt para o registro (formato vagas processo).
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
        Executa a exportação vagas processo, gera o arquivo e persiste conteúdo
        e nome no registro.
        """
        vagas_escolas = buscar_vagas_escolas(
            str(instance.processo_uuid),
            instance.cargo_codigo,
        )

        conteudo = formatar_arquivo_vagas_processo(
            instance.cargo_codigo, vagas_escolas
        )
        desc_safe = self.sanitizar_nome_arquivo(
            instance.processo_nome, max_len=60
        )
        cargo_safe = self.sanitizar_nome_arquivo(
            instance.cargo_nome, max_len=60
        )
        nome_arquivo = f"exportacao-vagas-processo-{cargo_safe}.{instance.cargo_codigo}.{desc_safe}.txt"  # noqa: E501
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.save(update_fields=["conteudo_arquivo", "nome_arquivo"])

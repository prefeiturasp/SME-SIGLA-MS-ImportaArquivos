"""ViewSet de exportação de candidatos por processo."""

from __future__ import annotations

from typing import Any

from django.http import HttpResponse

from exporta_arquivo.api.views.base import BaseExportacaoViewSet
from exporta_arquivo.models import ExportacaoCandidatosProcesso
from exporta_arquivo.repository import ExportacaoCandidatosProcessoRepository
from exporta_arquivo.serializers import (
    ExportacaoCandidatosProcessoCreateSerializer,
    ExportacaoCandidatosProcessoListSerializer,
)
from exporta_arquivo.services.exportacao_candidatos_processo import (
    exportar_candidatos_processo,
)


class ExportacaoCandidatosProcessoViewSet(BaseExportacaoViewSet):
    """ViewSet para exportação de candidatos por processo.

    - list: listagem (ou, se processo_uuid e cargo_uuid na query, retorna
      arquivo .txt; concurso_uuid opcional).
    - retrieve: detalhe de um registro.
    - create: cria registro e executa a exportação (persiste processo_uuid,
      cargo_uuid, concurso_*).
    - download (detail): retorna arquivo .txt da exportação.
    """

    queryset = ExportacaoCandidatosProcesso.objects.all()
    list_serializer_class = ExportacaoCandidatosProcessoListSerializer  # type: ignore[assignment]
    create_serializer_class = ExportacaoCandidatosProcessoCreateSerializer  # type: ignore[assignment]

    def gerar_arquivo(self, instance: Any) -> Any:
        """Gera arquivo.

        Args:
            instance: Instância do modelo em atualização.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        response = HttpResponse(
            instance.conteudo_arquivo.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{instance.nome_arquivo}"'
        )
        return response

    def executar_exportacao(self, instance: Any) -> None:
        """Busca candidatos, monta o arquivo e persiste conteúdo e nome.

        Args:
            instance: Instância do modelo em atualização.

        Returns:
            Nenhum valor; persiste alterações no banco.
        """
        conteudo = exportar_candidatos_processo(instance)
        desc_safe = self.sanitizar_nome_arquivo(
            instance.cargo_nome, max_len=60
        )
        nome_arquivo = (
            f"candidatos_processo_{desc_safe}_"
            f"{instance.concurso_codigo}.txt"
        )
        ExportacaoCandidatosProcessoRepository.atualizar(
            instance, conteudo_arquivo=conteudo, nome_arquivo=nome_arquivo
        )

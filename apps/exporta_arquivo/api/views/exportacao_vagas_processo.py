"""ViewSet de exportação de vagas por processo."""

from __future__ import annotations

from typing import Any

from django.http import HttpResponse

from exporta_arquivo.api.views.base import BaseExportacaoViewSet
from exporta_arquivo.models import ExportacaoVagasProcesso
from exporta_arquivo.repository import ExportacaoVagasProcessoRepository
from exporta_arquivo.serializers import (
    ExportacaoVagasProcessoCreateSerializer,
    ExportacaoVagasProcessoListSerializer,
)
from exporta_arquivo.services.exportacao_vagas_processo import (
    buscar_vagas_escolas as buscar_vagas_escolas_processo,
)
from exporta_arquivo.services.exportacao_vagas_processo import (
    formatar_arquivo_vagas_processo,
)


class ExportacaoVagasProcessoViewSet(BaseExportacaoViewSet):
    """ViewSet para exportação de vagas processo.

    - list: listagem (ou, se processo_uuid e cargo_uuid na query, retorna
      arquivo .txt — compatibilidade).
    - retrieve: detalhe de um registro.
    - create: cria registro e executa a exportação (persiste processo_uuid,
      cargo_uuid, concurso_*).
    - download (detail): retorna arquivo .txt da exportação.
    """

    queryset = ExportacaoVagasProcesso.objects.all()
    list_serializer_class = ExportacaoVagasProcessoListSerializer  # type: ignore[assignment]
    create_serializer_class = ExportacaoVagasProcessoCreateSerializer  # type: ignore[assignment]

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
        """Executa a exportação de vagas do processo.

        Gera o arquivo e persiste.

        Args:
            instance: Instância do modelo em atualização.

        Returns:
            Nenhum valor; persiste alterações no banco.
        """
        vagas_escolas = buscar_vagas_escolas_processo(
            str(instance.processo_uuid), instance.cargo_codigo
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
        ExportacaoVagasProcessoRepository.atualizar(
            instance, conteudo_arquivo=conteudo, nome_arquivo=nome_arquivo
        )

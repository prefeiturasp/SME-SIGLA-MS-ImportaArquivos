"""ViewSet de exportação de candidatos por processo.

- list: listagem (ou, se processo_uuid e cargo_uuid na query, retorna arquivo
.txt; concurso_uuid opcional).
- retrieve: detalhe de um registro.
- create: cria registro e executa a exportação (persiste processo_uuid,
cargo_uuid, concurso_*).
- download (detail): retorna arquivo .txt da exportação.
"""

from __future__ import annotations

from typing import Any

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
    """ViewSet para exportação de candidatos por processo."""

    queryset = ExportacaoCandidatosProcesso.objects.all()
    list_serializer_class = ExportacaoCandidatosProcessoListSerializer  # type: ignore[assignment]
    create_serializer_class = ExportacaoCandidatosProcessoCreateSerializer  # type: ignore[assignment]

    def gerar_arquivo(self, instance: Any) -> None:
        """Executa operação.

        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.

        Returns:
            Não retorna valor.

        Raises:
            Nenhuma exceção específica documentada.
        """
        conteudo = exportar_candidatos_processo(instance)
        desc_safe = self.sanitizar_nome_arquivo(
            instance.cargo_nome, max_len=60
        )
        nome_arquivo = (
            f"candidatos_processo_{desc_safe}_"
            f"{instance.concurso_codigo}.txt"
        )
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.save(update_fields=["conteudo_arquivo", "nome_arquivo"])

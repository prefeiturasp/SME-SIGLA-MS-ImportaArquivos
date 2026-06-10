"""ViewSet de exportação de vagas em formato vagas processo.

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
    """ViewSet para exportação de vagas processo."""

    queryset = ExportacaoVagasProcesso.objects.all()
    list_serializer_class = ExportacaoVagasProcessoListSerializer  # type: ignore[assignment]
    create_serializer_class = ExportacaoVagasProcessoCreateSerializer  # type: ignore[assignment]

    def gerar_arquivo(self, instance: Any) -> Any:
        """Gera arquivo.

        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.

        Returns:
            Valor calculado conforme a regra aplicada.
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
        """A exportação vagas processo, gera o arquivo e persiste.

        Args:
            self: Instância do objeto.
            instance: Instância do modelo em atualização.

        Returns:
            Nenhum valor.
        """
        vagas_escolas = buscar_vagas_escolas(
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
        instance.conteudo_arquivo = conteudo
        instance.nome_arquivo = nome_arquivo
        instance.save(update_fields=["conteudo_arquivo", "nome_arquivo"])

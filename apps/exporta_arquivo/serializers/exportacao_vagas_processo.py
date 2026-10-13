"""Módulo serializers/exportacao_vagas_processo."""

from core.serializers import PaginaSerializer
from rest_framework import serializers

from ..models import ExportacaoVagasProcesso
from .descricoes import DESCRICOES_EXPORTACAO


class ExportacaoVagasProcessoCreateSerializer(serializers.ModelSerializer):
    """Processo e cargo cujas vagas serão exportadas por unidade escolar."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoVagasProcesso
        fields = [
            "processo_uuid",
            "cargo_uuid",
            "concurso_uuid",
            "concurso_nome",
            "processo_nome",
            "cargo_nome",
            "cargo_codigo",
        ]
        extra_kwargs = DESCRICOES_EXPORTACAO


class ExportacaoVagasProcessoListSerializer(serializers.ModelSerializer):
    """Exportação de vagas por processo já registrada."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoVagasProcesso
        fields = [
            "uuid",
            "criado_em",
            "atualizado_em",
            "processo_uuid",
            "cargo_uuid",
            "concurso_uuid",
            "concurso_nome",
            "processo_nome",
            "cargo_nome",
            "cargo_codigo",
        ]
        read_only_fields = [
            "uuid",
            "criado_em",
            "atualizado_em",
            "processo_uuid",
            "cargo_uuid",
            "concurso_uuid",
            "concurso_nome",
            "processo_nome",
            "cargo_nome",
            "cargo_codigo",
        ]
        extra_kwargs = DESCRICOES_EXPORTACAO


class ExportacaoVagasProcessoPaginadoSerializer(PaginaSerializer):
    """Página da listagem de exportações de vagas por processo."""

    results = ExportacaoVagasProcessoListSerializer(
        many=True, help_text="Exportações da página."
    )

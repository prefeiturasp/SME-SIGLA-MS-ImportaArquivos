"""Módulo serializers/exportacao_candidatos_processo."""

from core.serializers import PaginaSerializer
from rest_framework import serializers

from ..models import ExportacaoCandidatosProcesso
from .descricoes import DESCRICOES_EXPORTACAO


class ExportacaoCandidatosProcessoCreateSerializer(
    serializers.ModelSerializer
):
    """Processo e cargo cujos candidatos habilitados serão exportados."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoCandidatosProcesso
        fields = [
            "processo_uuid",
            "cargo_uuid",
            "concurso_uuid",
            "concurso_nome",
            "processo_nome",
            "cargo_nome",
            "cargo_codigo",
            "concurso_codigo",
            "concurso_data_criacao",
        ]
        extra_kwargs = DESCRICOES_EXPORTACAO


class ExportacaoCandidatosProcessoListSerializer(serializers.ModelSerializer):
    """Exportação de candidatos por processo já registrada."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoCandidatosProcesso
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
            "concurso_codigo",
            "concurso_data_criacao",
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
            "concurso_codigo",
            "concurso_data_criacao",
        ]
        extra_kwargs = DESCRICOES_EXPORTACAO


class ExportacaoCandidatosProcessoPaginadoSerializer(PaginaSerializer):
    """Página da listagem de exportações de candidatos por processo."""

    results = ExportacaoCandidatosProcessoListSerializer(
        many=True, help_text="Exportações da página."
    )

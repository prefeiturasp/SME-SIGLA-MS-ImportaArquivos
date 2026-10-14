"""Módulo serializers/exportacao_vagas_sigpec."""

from __future__ import annotations

from typing import Any

from core.serializers import PaginaSerializer
from rest_framework import serializers

from ..models import ExportacaoVagasSigpec
from .descricoes import DESCRICOES_EXPORTACAO


class EscolaParaVagaSerializer(serializers.Serializer):
    """Serializer do modelo EscolaParaVaga."""

    codigo_integracao = serializers.CharField(
        trim_whitespace=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )
    codigo_eol = serializers.CharField(required=False)


class VagaInputSerializer(serializers.Serializer):
    """Valida cada item de vagas[], inclusive vagas definitivas."""

    vagas_definitivas = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
    vagas_precarias = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
    escola = EscolaParaVagaSerializer(required=True)
    cargo_codigo = serializers.IntegerField(required=True)


class VagasPayloadSerializer(serializers.Serializer):
    """Serializer do modelo VagasPayload."""

    vagas = VagaInputSerializer(many=True, required=True)

    def validate_vagas(self, value: Any) -> Any:
        """Valida vagas."""
        if not value:
            raise serializers.ValidationError(
                "Pelo menos uma vaga deve ser enviada."
            )
        return value


class ExportacaoVagasSigpecCreateSerializer(serializers.ModelSerializer):
    """Processo e cargo cujas vagas serão exportadas no formato SIGPEC."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoVagasSigpec
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


class ExportacaoVagasSigpecListSerializer(serializers.ModelSerializer):
    """Exportação de vagas SIGPEC já registrada."""

    class Meta:
        """Representa Meta."""

        model = ExportacaoVagasSigpec
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


class ExportacaoVagasSigpecPaginadoSerializer(PaginaSerializer):
    """Página da listagem de exportações de vagas SIGPEC."""

    results = ExportacaoVagasSigpecListSerializer(
        many=True, help_text="Exportações da página."
    )

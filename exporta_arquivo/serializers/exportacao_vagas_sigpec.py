"""Módulo serializers/exportacao_vagas_sigpec."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from ..models import ExportacaoVagasSigpec


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
        """Validate vagas.

        Args:
            self: Instância do objeto.
            value: Valor recebido para validação.

        Returns:
            Valor validado do campo vagas.

        Raises:
            ValidationError: Se os dados não passarem na validação.
        """
        if not value:
            raise serializers.ValidationError(
                "Pelo menos uma vaga deve ser enviada."
            )
        return value


class ExportacaoVagasSigpecCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de exportações de vagas SIGPEC."""

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


class ExportacaoVagasSigpecListSerializer(serializers.ModelSerializer):
    """Serializer para listagem e detalhe. cargo_nome e concurso_nome."""

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

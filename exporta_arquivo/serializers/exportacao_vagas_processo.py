"""Módulo serializers/exportacao_vagas_processo."""
from rest_framework import serializers

from ..models import ExportacaoVagasProcesso


class ExportacaoVagasProcessoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de exportações de vagas processo.

    Aceita processo_uuid, cargo_uuid, concurso_uuid (opcional), concurso_nome
    (opcional),
    processo_nome (opcional), cargo_nome (opcional), cargo_codigo
    (obrigatório).
    """

    class Meta:
        """Define Meta."""
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


class ExportacaoVagasProcessoListSerializer(serializers.ModelSerializer):
    """Serializer para listagem e detalhe. cargo_nome e concurso_nome apenas do.

    modelo (sem chamada a API).
    """

    class Meta:
        """Define Meta."""
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

"""Módulo serializers/exportacao_candidatos_processo."""
from rest_framework import serializers

from ..models import ExportacaoCandidatosProcesso


class ExportacaoCandidatosProcessoCreateSerializer(
    serializers.ModelSerializer
):
    """Serializer para criação de exportações de candidatos por processo.

    Aceita processo_uuid, cargo_uuid, concurso_uuid (opcional), concurso_nome
    (opcional),
    processo_nome (opcional), cargo_nome (opcional), cargo_codigo
    (obrigatório),
    concurso_codigo e concurso_data_criacao (opcionais).
    """

    class Meta:
        """Define Meta."""
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


class ExportacaoCandidatosProcessoListSerializer(serializers.ModelSerializer):
    """Serializer para listagem e detalhe. cargo_nome e concurso_nome apenas do.

    modelo (sem chamada a API).
    """

    class Meta:
        """Define Meta."""
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

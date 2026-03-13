from rest_framework import serializers
from ..models import ExportacaoVagasProcesso


class ExportacaoVagasProcessoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de exportações de vagas processo.
    Aceita processo_uuid, cargo_uuid, concurso_uuid (opcional), concurso_nome (opcional),
    processo_nome (opcional), cargo_nome (opcional), cargo_codigo (obrigatório).
    Aceita descricao_processo como alias de processo_nome (front envia descricao_processo).
    """
    descricao_processo = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = ExportacaoVagasProcesso
        fields = [
            'processo_uuid',
            'cargo_uuid',
            'concurso_uuid',
            'concurso_nome',
            'processo_nome',
            'cargo_nome',
            'cargo_codigo',
            'descricao_processo',
        ]

    def create(self, validated_data):
        descricao = validated_data.pop('descricao_processo', None)
        if descricao is not None and not (validated_data.get('processo_nome') or '').strip():
            validated_data['processo_nome'] = (descricao or '').strip() or None
        return super().create(validated_data)


class ExportacaoVagasProcessoListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem e detalhe. cargo_nome e concurso_nome apenas do modelo (sem chamada a API).
    """
    class Meta:
        model = ExportacaoVagasProcesso
        fields = [
            'uuid',
            'criado_em',
            'atualizado_em',
            'processo_uuid',
            'cargo_uuid',
            'concurso_uuid',
            'concurso_nome',
            'processo_nome',
            'cargo_nome',
            'cargo_codigo',
        ]
        read_only_fields = [
            'uuid',
            'criado_em',
            'atualizado_em',
            'processo_uuid',
            'cargo_uuid',
            'concurso_uuid',
            'concurso_nome',
            'processo_nome',
            'cargo_nome',
            'cargo_codigo',
        ]

from rest_framework import serializers

from ..models import ExportacaoVagasSigpec


class EscolaParaVagaSerializer(serializers.Serializer):
    codigo_integracao = serializers.CharField(
        trim_whitespace=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        default="",
    )

    codigo_eol = serializers.CharField(required=False)


class VagaInputSerializer(serializers.Serializer):
    """
    Valida cada objeto dentro de vagas[] com foco em vagas_definitivas,
    vagas_precarias e escola.codigo_integracao.
    """

    vagas_definitivas = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
    vagas_precarias = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
    escola = EscolaParaVagaSerializer(required=True)
    cargo_codigo = serializers.IntegerField(required=True)


class VagasPayloadSerializer(serializers.Serializer):
    vagas = VagaInputSerializer(many=True, required=True)

    def validate_vagas(self, value):
        if not value:
            raise serializers.ValidationError(
                "Pelo menos uma vaga deve ser enviada."
            )
        return value


class ExportacaoVagasSigpecCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de exportações de vagas SIGPEC.
    Aceita processo_uuid, cargo_uuid, concurso_uuid (opcional), concurso_nome
    (opcional),
    processo_nome (opcional), cargo_nome (opcional), cargo_codigo
    (obrigatório).
    """

    class Meta:
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
    """
    Serializer para listagem e detalhe. cargo_nome e concurso_nome apenas do
    modelo (sem chamada a API).
    """

    class Meta:
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

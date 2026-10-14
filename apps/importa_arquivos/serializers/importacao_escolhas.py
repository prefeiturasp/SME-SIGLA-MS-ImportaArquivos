"""Módulo serializers/importacao_escolhas."""

from __future__ import annotations

from typing import Any

from core.serializers import PaginaSerializer
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import ImportacaoErro, ImportacaoEscolhas
from .descricoes import DESCRICAO_ERROS, DESCRICOES_IMPORTACAO
from .importacao_erros import ErroDaImportacaoSerializer


class ImportacaoEscolhasCreateSerializer(serializers.Serializer):
    """Processo de convocação cujas escolhas serão buscadas na PRODAM."""

    processo_uuid = serializers.UUIDField(
        required=True,
        help_text=(
            "UUID do processo de convocação (MS-ProcessosConvocacao) que "
            "receberá as escolhas."
        ),
    )
    processo_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text=(
            "Identificador do processo de convocação na PRODAM. Quando não "
            "é enviado, o serviço usa 819."
        ),
    )
    concurso_uuid = serializers.UUIDField(
        required=True, help_text="UUID do concurso (MS-Concursos)."
    )


class ImportacaoEscolhasListSerializer(serializers.ModelSerializer):
    """Importação de escolhas, com os dados da PRODAM e o resultado."""

    erros = serializers.SerializerMethodField(help_text=DESCRICAO_ERROS)
    processo_nome = serializers.SerializerMethodField(
        help_text="Nome do processo de convocação. Hoje vem sempre nulo."
    )
    _content_type_cache = None

    class Meta:
        """Representa Meta."""

        model = ImportacaoEscolhas
        fields = [
            "uuid",
            "processo_uuid",
            "processo_id",
            "dados_prodam",
            "status",
            "modo",
            "criado_em",
            "atualizado_em",
            "erros",
            "concurso_uuid",
            "processo_nome",
        ]
        read_only_fields = [
            "uuid",
            "criado_em",
            "atualizado_em",
            "erros",
            "processo_nome",
        ]
        extra_kwargs = DESCRICOES_IMPORTACAO

    @extend_schema_field(
        ErroDaImportacaoSerializer(many=True, allow_null=True)
    )
    def get_erros(self, obj: Any) -> Any:
        """Obtém erros vinculados à importação de escolhas."""
        if ImportacaoEscolhasListSerializer._content_type_cache is None:
            ImportacaoEscolhasListSerializer._content_type_cache = (
                ContentType.objects.get_for_model(ImportacaoEscolhas)
            )
        erros_queryset = ImportacaoErro.objects.filter(
            content_type=ImportacaoEscolhasListSerializer._content_type_cache,
            object_id=obj.uuid,
        ).order_by("-criado_em")
        if not erros_queryset.exists():
            return None
        erros_list = []
        for erro in erros_queryset:
            erros_list.append(
                {
                    "mensagem": erro.mensagem,
                    "erros": erro.erros,
                    "criado_em": erro.criado_em,
                }
            )
        return erros_list

    @extend_schema_field({"type": "string", "nullable": True})
    def get_processo_nome(self, obj: Any) -> Any:
        """Obtém nome do processo associado à importação de escolhas."""
        return None


class ImportacaoEscolhasPaginadoSerializer(PaginaSerializer):
    """Página da listagem de importações de escolhas."""

    results = ImportacaoEscolhasListSerializer(
        many=True, help_text="Importações de escolhas da página."
    )


class ResponseSerializer(serializers.Serializer):
    """Serializer para validar resposta da API externa."""

    retorno = serializers.CharField(required=True)
    mensagem = serializers.CharField(required=True)
    # Nome mantido em mixedCase: espelha a chave do payload da API Prodam;
    # DRF lê o dado de entrada pelo nome do campo, não por `source=`.
    lstDadosResultadoConvocacaoIngresso = serializers.ListField(  # noqa: N815
        child=serializers.DictField(), required=True, allow_empty=True
    )

    def validate_lstDadosResultadoConvocacaoIngresso(  # noqa: N802
        self, value: Any
    ) -> Any:
        """Valida lstDadosResultadoConvocacaoIngresso."""
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    "Cada item deve ser um dicionário"
                )
            required_fields = [
                "codigoPessoaFisica",
                "codigoCargo",
                "descricaoStatus",
            ]
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(
                        f"Campo obrigatório ausente: {field}"
                    )
        return value


class EscolhaItemSerializer(serializers.Serializer):
    """Serializer para item de escolha."""

    # Nomes mantidos em mixedCase: espelham as chaves do payload da API
    # Prodam; DRF lê o dado de entrada pelo nome do campo, não por `source=`.
    codigoPessoaFisica = serializers.CharField()  # noqa: N815
    codigoCargo = serializers.CharField()  # noqa: N815
    codigoUnidadeAlocacao = serializers.CharField(  # noqa: N815
        allow_null=True, required=False
    )
    tipoVaga = serializers.CharField(  # noqa: N815
        allow_null=True, required=False
    )
    descricaoStatus = serializers.CharField()  # noqa: N815


class EscolhasImportacaoSerializer(serializers.Serializer):
    """Serializer para enviar dados ao MS-Escolhas."""

    processo_uuid = serializers.UUIDField(required=True)
    concurso_uuid = serializers.UUIDField(required=True)
    escolhas = serializers.ListField(
        child=serializers.DictField(), required=True
    )

    def validate_escolhas(self, value: Any) -> Any:
        """Valida escolhas."""
        for escolha in value:
            required_fields = ["cpf", "codigo_cargo", "situacao"]
            for field in required_fields:
                if field not in escolha:
                    raise serializers.ValidationError(
                        f"Campo obrigatório ausente na escolha: {field}"
                    )
        return value

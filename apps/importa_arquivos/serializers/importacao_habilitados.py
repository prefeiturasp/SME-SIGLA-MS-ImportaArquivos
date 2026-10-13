"""Módulo serializers/importacao_habilitados."""

from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import ImportacaoArquivoHabilitado, ImportacaoErro
from .descricoes import DESCRICAO_ERROS, DESCRICOES_IMPORTACAO
from .importacao_erros import ErroDaImportacaoSerializer


class ImportacaoArquivoHabilitadosCreateSerializer(
    serializers.ModelSerializer
):
    """Dados enviados na importação de habilitados."""

    mandado_judicial = serializers.BooleanField(
        required=False,
        default=False,
        write_only=True,
        help_text=(
            "Indica que os habilitados do arquivo entram por mandado "
            "judicial. É repassado ao MS-Candidatos e não fica gravado na "
            "importação."
        ),
    )

    class Meta:
        """Representa Meta."""

        model = ImportacaoArquivoHabilitado
        fields = [
            "arquivo",
            "concurso_uuid",
            "concurso_nome",
            "observacao",
            "mandado_judicial",
        ]
        extra_kwargs = {
            **DESCRICOES_IMPORTACAO,
            "arquivo": {
                "help_text": (
                    "Arquivo CSV de habilitados, separado por vírgula e em "
                    "UTF-8. Nas respostas, vem a URL do arquivo armazenado."
                )
            },
        }

    def create(self, validated_data: Any) -> Any:
        """Cria e persiste o registro a partir dos dados validados."""
        validated_data.pop("mandado_judicial", False)
        arquivo = validated_data.get("arquivo")
        nome_arquivo = (
            getattr(arquivo, "name", None) or "Importação de Habilitados"
        )
        instance = ImportacaoArquivoHabilitado.objects.create(
            nome_arquivo=nome_arquivo, tipo="HABILITADOS", **validated_data
        )
        return instance


class ImportacaoArquivoHabilitadosListSerializer(serializers.ModelSerializer):
    """Importação de habilitados, com o resultado do processamento."""

    erros = serializers.SerializerMethodField(help_text=DESCRICAO_ERROS)
    _content_type_cache = None

    class Meta:
        """Representa Meta."""

        model = ImportacaoArquivoHabilitado
        fields = [
            "uuid",
            "nome_arquivo",
            "arquivo",
            "status",
            "concurso_uuid",
            "concurso_nome",
            "observacao",
            "quantidade",
            "criado_em",
            "atualizado_em",
            "erros",
        ]
        read_only_fields = [
            "uuid",
            "quantidade",
            "criado_em",
            "atualizado_em",
            "erros",
        ]
        extra_kwargs = DESCRICOES_IMPORTACAO

    @extend_schema_field(
        ErroDaImportacaoSerializer(many=True, allow_null=True)
    )
    def get_erros(self, obj: Any) -> Any:
        """Obtém erros vinculados à importação de habilitados."""
        if (
            ImportacaoArquivoHabilitadosListSerializer._content_type_cache
            is None
        ):
            ImportacaoArquivoHabilitadosListSerializer._content_type_cache = (
                ContentType.objects.get_for_model(ImportacaoArquivoHabilitado)
            )
        erros_queryset = ImportacaoErro.objects.filter(
            content_type=ImportacaoArquivoHabilitadosListSerializer._content_type_cache,
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

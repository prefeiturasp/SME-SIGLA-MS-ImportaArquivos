"""Módulo serializers/importacao_lotes."""

from __future__ import annotations

from typing import Any

from core.serializers import PaginaSerializer
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import ImportacaoErro, ImportacaoLotes
from .descricoes import DESCRICAO_ERROS, DESCRICOES_IMPORTACAO
from .importacao_erros import ErroDaImportacaoSerializer


class ImportacaoLotesCreateSerializer(serializers.ModelSerializer):
    """Dados enviados na importação de lotes."""

    class Meta:
        """Representa Meta."""

        model = ImportacaoLotes
        fields = ["arquivo", "concurso_uuid", "concurso_nome"]
        extra_kwargs = {
            **DESCRICOES_IMPORTACAO,
            "arquivo": {
                "help_text": (
                    "Arquivo TXT de lotes do SIGPEC, separado por ponto e "
                    "vírgula. Nas respostas, vem a URL do arquivo "
                    "armazenado."
                )
            },
        }

    def create(self, validated_data: Any) -> Any:
        """Cria e persiste o registro a partir dos dados validados."""
        arquivo = validated_data.get("arquivo")
        nome_arquivo = getattr(arquivo, "name", None) or "Importação de Lotes"
        instance = ImportacaoLotes.objects.create(
            nome_arquivo=nome_arquivo,
            tipo="LOTES",
            status="PENDENTE",
            **validated_data,
        )
        return instance


class ImportacaoLotesListSerializer(serializers.ModelSerializer):
    """Importação de lotes, com o resultado do processamento."""

    erros = serializers.SerializerMethodField(help_text=DESCRICAO_ERROS)
    _content_type_cache = None

    class Meta:
        """Representa Meta."""

        model = ImportacaoLotes
        fields = [
            "uuid",
            "nome_arquivo",
            "arquivo",
            "tipo",
            "concurso_uuid",
            "concurso_nome",
            "status",
            "total_atualizados",
            "erros",
            "detalhes",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "uuid",
            "tipo",
            "criado_em",
            "atualizado_em",
            "status",
            "total_atualizados",
            "detalhes",
        ]
        extra_kwargs = DESCRICOES_IMPORTACAO

    @extend_schema_field(
        ErroDaImportacaoSerializer(many=True, allow_null=True)
    )
    def get_erros(self, obj: Any) -> Any:
        """Obtém erros vinculados à importação de lotes."""
        if ImportacaoLotesListSerializer._content_type_cache is None:
            ImportacaoLotesListSerializer._content_type_cache = (
                ContentType.objects.get_for_model(ImportacaoLotes)
            )
        erros_qs = ImportacaoErro.objects.filter(
            content_type=ImportacaoLotesListSerializer._content_type_cache,
            object_id=obj.uuid,
        ).order_by("-criado_em")
        if not erros_qs.exists():
            return None
        return [
            {
                "mensagem": e.mensagem,
                "erros": e.erros,
                "criado_em": e.criado_em,
            }
            for e in erros_qs
        ]


class ImportacaoLotesPaginadoSerializer(PaginaSerializer):
    """Página da listagem de importações de lotes."""

    results = ImportacaoLotesListSerializer(
        many=True, help_text="Importações de lotes da página."
    )

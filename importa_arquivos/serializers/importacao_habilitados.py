"""Módulo serializers/importacao_habilitados."""

from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from ..models import ImportacaoArquivoHabilitado, ImportacaoErro


class ImportacaoArquivoHabilitadosCreateSerializer(
    serializers.ModelSerializer
):
    """Serializer para criação de importações de arquivos habilitados."""

    class Meta:
        """Representa Meta."""

        model = ImportacaoArquivoHabilitado
        fields = ["arquivo", "concurso_uuid", "concurso_nome"]

    def create(self, validated_data: Any) -> Any:
        """Cria e persiste o registro a partir dos dados validados.

        Args:
            self: Instância do objeto.
            validated_data: Dados validados pelo serializer.

        Returns:
            Instância criada e persistida no banco.
        """
        arquivo = validated_data.get("arquivo")
        nome_arquivo = (
            getattr(arquivo, "name", None) or "Importação de Habilitados"
        )
        instance = ImportacaoArquivoHabilitado.objects.create(
            nome_arquivo=nome_arquivo, tipo="HABILITADOS", **validated_data
        )
        return instance


class ImportacaoArquivoHabilitadosListSerializer(serializers.ModelSerializer):
    """Serializer para listagem/detalhe com todos os campos do modelo."""

    erros = serializers.SerializerMethodField()
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
            "criado_em",
            "atualizado_em",
            "erros",
        ]
        read_only_fields = ["uuid", "criado_em", "atualizado_em", "erros"]

    def get_erros(self, obj: Any) -> Any:
        """Obtém erros vinculados à importação.

        Args:
            obj: Instância da importação em listagem.

        Returns:
            Lista de erros da importação ou None se vazio.
        """
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

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from ..models import ImportacaoArquivoVagas, ImportacaoErro


class ImportacaoArquivoVagasCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação para importações de vagas."""

    class Meta:
        model = ImportacaoArquivoVagas
        fields = ["arquivo", "processo_uuid", "processo_nome"]

    def create(self, validated_data):
        arquivo = validated_data.get("arquivo")
        nome_arquivo = getattr(arquivo, "name", None) or "Importação de Vagas"
        instance = ImportacaoArquivoVagas.objects.create(
            nome_arquivo=nome_arquivo,
            tipo="VAGAS",
            **validated_data,
        )
        return instance


class ImportacaoArquivoVagasListSerializer(serializers.ModelSerializer):
    """
    Serializer de listagem/detalhe para importações de vagas (todos os campos).
    """

    erros = serializers.SerializerMethodField()

    _content_type_cache = None

    class Meta:
        model = ImportacaoArquivoVagas
        fields = [
            "uuid",
            "nome_arquivo",
            "arquivo",
            "status",
            "processo_uuid",
            "processo_nome",
            "criado_em",
            "atualizado_em",
            "erros",
        ]
        read_only_fields = ["uuid", "criado_em", "atualizado_em", "erros"]

    def get_erros(self, obj):
        """Retorna os erros associados à importação, se existirem."""
        if ImportacaoArquivoVagasListSerializer._content_type_cache is None:
            ImportacaoArquivoVagasListSerializer._content_type_cache = (
                ContentType.objects.get_for_model(ImportacaoArquivoVagas)
            )

        erros_queryset = ImportacaoErro.objects.filter(
            content_type=ImportacaoArquivoVagasListSerializer._content_type_cache,
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

from rest_framework import serializers
from ..models import ImportacaoArquivoVagas


class ImportacaoArquivoVagasCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação para importações de vagas."""
    class Meta:
        model = ImportacaoArquivoVagas
        fields = [
            'arquivo', 'concurso_uuid', 'concurso_nome'
        ]

    def create(self, validated_data):
        arquivo = validated_data.get('arquivo')
        nome_arquivo = getattr(arquivo, 'name', None) or 'Importação de Vagas'
        instance = ImportacaoArquivoVagas.objects.create(
            nome_arquivo=nome_arquivo,
            tipo='VAGAS',
            **validated_data,
        )
        return instance


class ImportacaoArquivoVagasListSerializer(serializers.ModelSerializer):
    """Serializer de listagem/detalhe para importações de vagas (todos os campos)."""
    class Meta:
        model = ImportacaoArquivoVagas
        fields = [
            'uuid', 'nome_arquivo', 'arquivo', 'status', 'concurso_uuid', 'concurso_nome',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']

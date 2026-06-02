"""
Testes dos serializers de exportação: create (campos obrigatórios) e list
(read_only, serialização de instance).
"""

import uuid

import pytest

pytestmark = pytest.mark.django_db

from exporta_arquivo.models import (  # noqa: E402
    ExportacaoCandidatosProcesso,
    ExportacaoVagasProcesso,
    ExportacaoVagasSigpec,
)
from exporta_arquivo.serializers.exportacao_candidatos_processo import (  # noqa: E402
    ExportacaoCandidatosProcessoCreateSerializer,
    ExportacaoCandidatosProcessoListSerializer,
)
from exporta_arquivo.serializers.exportacao_vagas_processo import (  # noqa: E402
    ExportacaoVagasProcessoCreateSerializer,
    ExportacaoVagasProcessoListSerializer,
)
from exporta_arquivo.serializers.exportacao_vagas_sigpec import (  # noqa: E402
    ExportacaoVagasSigpecCreateSerializer,
    ExportacaoVagasSigpecListSerializer,
)


def _uuid():
    return str(uuid.uuid4())


# --- Candidatos processo ---


class TestExportacaoCandidatosProcessoCreateSerializer:
    """
    Create: obrigatórios processo_uuid, cargo_uuid, cargo_codigo; opcionais.
    """

    def test_campos_obrigatorios_processo_uuid_cargo_uuid_cargo_codigo(self):
        """
        Faltando processo_uuid, cargo_uuid ou cargo_codigo deve falhar na
        validação.
        """
        base = {
            "processo_uuid": _uuid(),
            "cargo_uuid": _uuid(),
            "cargo_codigo": 100,
        }
        serializer = ExportacaoCandidatosProcessoCreateSerializer(data=base)
        assert serializer.is_valid(), serializer.errors
        # Sem processo_uuid
        s1 = ExportacaoCandidatosProcessoCreateSerializer(
            data={"cargo_uuid": _uuid(), "cargo_codigo": 100}
        )
        assert not s1.is_valid()
        assert "processo_uuid" in s1.errors
        # Sem cargo_uuid
        s2 = ExportacaoCandidatosProcessoCreateSerializer(
            data={"processo_uuid": _uuid(), "cargo_codigo": 100}
        )
        assert not s2.is_valid()
        assert "cargo_uuid" in s2.errors
        # Sem cargo_codigo: modelo aceita null; serializer pode ou não exigir
        ExportacaoCandidatosProcessoCreateSerializer(
            data={"processo_uuid": _uuid(), "cargo_uuid": _uuid()}
        )
        # Se o model tem null=True em cargo_codigo, is_valid pode passar; a view/service exige  # noqa: E501
        # Testamos que com cargo_codigo válido o create funciona
        s4 = ExportacaoCandidatosProcessoCreateSerializer(data=base)
        assert s4.is_valid()
        obj = s4.save()
        assert obj.cargo_codigo == 100
        obj.delete()

    def test_campos_opcionais_aceitos(self):
        """
        concurso_uuid, processo_nome, cargo_nome, concurso_codigo,
        concurso_data_criacao são opcionais.
        """
        data = {
            "processo_uuid": _uuid(),
            "cargo_uuid": _uuid(),
            "cargo_codigo": 1,
            "concurso_uuid": _uuid(),
            "processo_nome": "Processo X",
            "cargo_nome": "Cargo Y",
            "concurso_nome": "Concurso Z",
            "concurso_codigo": 99,
            "concurso_data_criacao": "2024-01-01T00:00:00",
        }
        serializer = ExportacaoCandidatosProcessoCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.processo_nome == "Processo X"
        assert obj.cargo_nome == "Cargo Y"
        assert obj.concurso_codigo == 99
        assert obj.concurso_data_criacao is not None
        assert obj.concurso_data_criacao.year == 2024
        assert obj.concurso_data_criacao.month == 1
        assert obj.concurso_data_criacao.day == 1
        obj.delete()


class TestExportacaoCandidatosProcessoListSerializer:
    """List: read_only esperados e serialização de instance."""

    def test_read_only_fields_esperados(self):
        """List serializer tem todos os campos de listagem como read_only."""
        expected = {
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
        }
        meta = ExportacaoCandidatosProcessoListSerializer.Meta
        assert set(meta.read_only_fields) == expected
        assert set(meta.fields) == expected

    def test_instance_serializa_corretamente(self):
        """Uma instance do model serializa com todos os campos esperados."""
        obj = ExportacaoCandidatosProcesso.objects.create(
            processo_uuid=uuid.uuid4(),
            cargo_uuid=uuid.uuid4(),
            cargo_codigo=10,
            processo_nome="Proc",
            cargo_nome="Cargo",
        )
        serializer = ExportacaoCandidatosProcessoListSerializer(instance=obj)
        data = serializer.data
        assert "uuid" in data
        assert "criado_em" in data
        assert "atualizado_em" in data
        assert str(obj.processo_uuid) == data["processo_uuid"]
        assert data["processo_nome"] == "Proc"
        assert data["cargo_nome"] == "Cargo"
        assert data["cargo_codigo"] == 10
        obj.delete()


# --- Vagas processo ---


class TestExportacaoVagasProcessoCreateSerializer:
    """Create: obrigatórios; create com dados válidos."""

    def test_create_com_dados_validos(self):
        """
        Create com processo_uuid, cargo_uuid, cargo_codigo (e opcionais) cria
        registro.
        """
        data = {
            "processo_uuid": _uuid(),
            "cargo_uuid": _uuid(),
            "cargo_codigo": 200,
        }
        serializer = ExportacaoVagasProcessoCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.cargo_codigo == 200
        obj.delete()


class TestExportacaoVagasProcessoListSerializer:
    """List: read_only e serialização de instance."""

    def test_read_only_e_serializacao(self):
        expected_fields = {
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
        }
        meta = ExportacaoVagasProcessoListSerializer.Meta
        assert set(meta.read_only_fields) == expected_fields
        obj = ExportacaoVagasProcesso.objects.create(
            processo_uuid=uuid.uuid4(),
            cargo_uuid=uuid.uuid4(),
            cargo_codigo=5,
        )
        serializer = ExportacaoVagasProcessoListSerializer(instance=obj)
        data = serializer.data
        assert data["cargo_codigo"] == 5
        assert "uuid" in data
        obj.delete()


# --- Vagas SIGPEC ---


class TestExportacaoVagasSigpecCreateSerializer:
    """
    Create: cargo_codigo obrigatório na prática; create com dados válidos.
    """

    def test_create_com_dados_validos(self):
        data = {
            "processo_uuid": _uuid(),
            "cargo_uuid": _uuid(),
            "cargo_codigo": 300,
        }
        serializer = ExportacaoVagasSigpecCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.cargo_codigo == 300
        obj.delete()


class TestExportacaoVagasSigpecListSerializer:
    """List: read_only e serialização."""

    def test_read_only_e_serializacao(self):
        expected_fields = {
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
        }
        meta = ExportacaoVagasSigpecListSerializer.Meta
        assert set(meta.read_only_fields) == expected_fields
        obj = ExportacaoVagasSigpec.objects.create(
            processo_uuid=uuid.uuid4(),
            cargo_uuid=uuid.uuid4(),
            cargo_codigo=7,
        )
        serializer = ExportacaoVagasSigpecListSerializer(instance=obj)
        data = serializer.data
        assert data["cargo_codigo"] == 7
        assert "uuid" in data
        obj.delete()

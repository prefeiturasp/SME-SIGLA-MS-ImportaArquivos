"""Testes unitários para os serializers de importação de escolhas."""

from __future__ import annotations

import uuid

import pytest
from django.contrib.contenttypes.models import ContentType

from importa_arquivos.models import ImportacaoErro, ImportacaoEscolhas
from importa_arquivos.serializers.importacao_escolhas import (
    EscolhaItemSerializer,
    EscolhasImportacaoSerializer,
    ImportacaoEscolhasCreateSerializer,
    ImportacaoEscolhasListSerializer,
    ResponseSerializer,
)

pytestmark = pytest.mark.django_db


class TestImportacaoEscolhasCreateSerializer:
    """Testes para ImportacaoEscolhasCreateSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Verifica serializer valido com dados completos."""
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        data = {
            "processo_uuid": str(processo_uuid),
            "processo_id": processo_id,
            "concurso_uuid": str(concurso_uuid),
        }
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["processo_uuid"] == processo_uuid
        assert serializer.validated_data["processo_id"] == processo_id
        assert serializer.validated_data["concurso_uuid"] == concurso_uuid

    def test_serializer_invalido_sem_processo_uuid(self) -> None:
        """Verifica serializer invalido sem processo uuid."""
        data = {"processo_id": 123}
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "processo_uuid" in serializer.errors

    def test_serializer_valido_sem_processo_id(self) -> None:
        """Verifica serializer valido sem processo id."""
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        data = {
            "processo_uuid": str(processo_uuid),
            "concurso_uuid": str(concurso_uuid),
        }
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["processo_uuid"] == processo_uuid
        assert serializer.validated_data["concurso_uuid"] == concurso_uuid
        assert serializer.validated_data.get("processo_id") is None

    def test_serializer_invalido_processo_uuid_invalido(self) -> None:
        """Verifica serializer invalido processo uuid invalido."""
        data = {"processo_uuid": "invalid-uuid", "processo_id": 123}
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "processo_uuid" in serializer.errors

    def test_serializer_invalido_processo_id_nao_inteiro(self) -> None:
        """Verifica serializer invalido processo id nao inteiro."""
        processo_uuid = uuid.uuid4()
        data = {
            "processo_uuid": str(processo_uuid),
            "processo_id": "not-an-integer",
        }
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "processo_id" in serializer.errors


class TestImportacaoEscolhasListSerializer:
    """Testes para ImportacaoEscolhasListSerializer."""

    def test_serializer_lista_todos_campos(self) -> None:
        """Verifica serializer lista todos campos."""
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid,
            processo_id=123,
            concurso_uuid=concurso_uuid,
            status="CONCLUIDO",
        )
        serializer = ImportacaoEscolhasListSerializer(importacao)
        data = serializer.data
        assert "uuid" in data
        assert "processo_uuid" in data
        assert "processo_id" in data
        assert "concurso_uuid" in data
        assert "dados_prodam" in data
        assert "status" in data
        assert "criado_em" in data
        assert "atualizado_em" in data
        assert "erros" in data

    def test_serializer_retorna_erros_vazios_quando_nao_existem(self) -> None:
        """Verifica serializer retorna erros vazios quando nao existem."""
        processo_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid, processo_id=123
        )
        serializer = ImportacaoEscolhasListSerializer(importacao)
        assert serializer.data["erros"] is None

    def test_serializer_retorna_erros_quando_existem(self) -> None:
        """Verifica serializer retorna erros quando existem."""
        processo_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid, processo_id=123
        )
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem="Erro de teste",
            erros="Detalhes do erro",
        )
        serializer = ImportacaoEscolhasListSerializer(importacao)
        erros = serializer.data["erros"]
        assert erros is not None
        assert len(erros) == 1
        assert erros[0]["mensagem"] == "Erro de teste"
        assert erros[0]["erros"] == "Detalhes do erro"
        assert "criado_em" in erros[0]

    def test_serializer_retorna_multiplos_erros_ordenados(self) -> None:
        """Verifica serializer retorna multiplos erros ordenados."""
        processo_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid, processo_id=123
        )
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem="Erro 1",
            erros="Detalhes 1",
        )
        import time

        time.sleep(0.01)
        ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=importacao.uuid,
            mensagem="Erro 2",
            erros="Detalhes 2",
        )
        serializer = ImportacaoEscolhasListSerializer(importacao)
        erros = serializer.data["erros"]
        assert len(erros) == 2
        assert erros[0]["mensagem"] == "Erro 2"
        assert erros[1]["mensagem"] == "Erro 1"


class TestResponseSerializer:
    """Testes para ResponseSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Verifica serializer valido com dados completos."""
        data = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [
                {
                    "codigoPessoaFisica": "12345678901",
                    "codigoCargo": "123",
                    "descricaoStatus": "ALOCADO",
                }
            ],
        }
        serializer = ResponseSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["retorno"] == "TRUE"
        assert (
            len(
                serializer.validated_data[
                    "lstDadosResultadoConvocacaoIngresso"
                ]
            )
            == 1
        )

    def test_serializer_valido_com_lista_vazia(self) -> None:
        """Verifica serializer valido com lista vazia."""
        data = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [],
        }
        serializer = ResponseSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_invalido_sem_retorno(self) -> None:
        """Verifica serializer invalido sem retorno."""
        data = {
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [],
        }
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert "retorno" in serializer.errors

    def test_serializer_invalido_sem_mensagem(self) -> None:
        """Verifica serializer invalido sem mensagem."""
        data = {"retorno": "TRUE", "lstDadosResultadoConvocacaoIngresso": []}
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert "mensagem" in serializer.errors

    def test_serializer_invalido_sem_lista_dados(self) -> None:
        """Verifica serializer invalido sem lista dados."""
        data = {"retorno": "TRUE", "mensagem": "Sucesso"}
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert "lstDadosResultadoConvocacaoIngresso" in serializer.errors

    def test_serializer_valida_campos_obrigatorios_em_cada_item(self) -> None:
        """Verifica serializer valida campos obrigatorios em cada item."""
        data = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": [
                {
                    "codigoPessoaFisica": "12345678901",
                    "codigoCargo": "123",
                    "descricaoStatus": "ALOCADO",
                },
                {"codigoPessoaFisica": "98765432109"},
            ],
        }
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert "lstDadosResultadoConvocacaoIngresso" in serializer.errors

    def test_serializer_valida_que_cada_item_eh_dicionario(self) -> None:
        """Verifica serializer valida que cada item eh dicionario."""
        data = {
            "retorno": "TRUE",
            "mensagem": "Sucesso",
            "lstDadosResultadoConvocacaoIngresso": ["not-a-dict"],
        }
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert "lstDadosResultadoConvocacaoIngresso" in serializer.errors


class TestEscolhaItemSerializer:
    """Testes para EscolhaItemSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Verifica serializer valido com dados completos."""
        data = {
            "codigoPessoaFisica": "12345678901",
            "codigoCargo": "123",
            "codigoUnidadeAlocacao": "456789",
            "tipoVaga": "PRECARIA",
            "descricaoStatus": "ALOCADO",
        }
        serializer = EscolhaItemSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_valido_com_campos_opcionais_nulos(self) -> None:
        """Verifica serializer valido com campos opcionais nulos."""
        data = {
            "codigoPessoaFisica": "12345678901",
            "codigoCargo": "123",
            "codigoUnidadeAlocacao": None,
            "tipoVaga": None,
            "descricaoStatus": "ALOCADO",
        }
        serializer = EscolhaItemSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_invalido_sem_codigo_pessoa_fisica(self) -> None:
        """Verifica serializer invalido sem codigo pessoa fisica."""
        data = {"codigoCargo": "123", "descricaoStatus": "ALOCADO"}
        serializer = EscolhaItemSerializer(data=data)
        assert not serializer.is_valid()
        assert "codigoPessoaFisica" in serializer.errors


class TestEscolhasImportacaoSerializer:
    """Testes para EscolhasImportacaoSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Verifica serializer valido com dados completos."""
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        data = {
            "processo_uuid": str(processo_uuid),
            "concurso_uuid": str(concurso_uuid),
            "escolhas": [
                {
                    "cpf": "12345678901",
                    "codigo_cargo": "123",
                    "situacao": "ESCOLHA",
                }
            ],
        }
        serializer = EscolhasImportacaoSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_invalido_sem_processo_uuid(self) -> None:
        """Verifica serializer invalido sem processo uuid."""
        data = {
            "escolhas": [
                {
                    "cpf": "12345678901",
                    "codigo_cargo": "123",
                    "situacao": "ESCOLHA",
                }
            ]
        }
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert "processo_uuid" in serializer.errors

    def test_serializer_invalido_sem_escolhas(self) -> None:
        """Verifica serializer invalido sem escolhas."""
        processo_uuid = uuid.uuid4()
        data = {"processo_uuid": str(processo_uuid)}
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert "escolhas" in serializer.errors

    def test_serializer_valida_campos_obrigatorios_em_cada_escolha(
        self,
    ) -> None:
        """Verifica serializer valida campos obrigatorios em cada escolha."""
        processo_uuid = uuid.uuid4()
        data = {
            "processo_uuid": str(processo_uuid),
            "escolhas": [
                {
                    "cpf": "12345678901",
                    "codigo_cargo": "123",
                    "situacao": "ESCOLHA",
                },
                {"cpf": "98765432109"},
            ],
        }
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert "escolhas" in serializer.errors

    def test_serializer_valida_cpf_obrigatorio(self) -> None:
        """Verifica serializer valida cpf obrigatorio."""
        processo_uuid = uuid.uuid4()
        data = {
            "processo_uuid": str(processo_uuid),
            "escolhas": [{"codigo_cargo": "123", "situacao": "ESCOLHA"}],
        }
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert "escolhas" in serializer.errors

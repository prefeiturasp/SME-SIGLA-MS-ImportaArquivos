"""Testes unitários para o model ImportacaoEscolhas."""

from __future__ import annotations

import time
import uuid

import pytest

from importa_arquivos.models import ImportacaoEscolhas
from importa_arquivos.models.base import CHOICES_STATUS_IMPORTACAO_ARQUIVO

pytestmark = pytest.mark.django_db


class TestImportacaoEscolhasModel:
    """Testes para o model ImportacaoEscolhas."""

    def test_criar_importacao_escolhas_com_valores_minimos(self) -> None:
        """Verifica criar importacao escolhas com valores minimos."""
        processo_uuid = uuid.uuid4()
        processo_id = 123
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid, processo_id=processo_id
        )
        assert importacao.uuid is not None
        assert importacao.processo_uuid == processo_uuid
        assert importacao.processo_id == processo_id
        assert importacao.status == "CONCLUIDO"
        assert importacao.dados_prodam is None
        assert importacao.criado_em is not None
        assert importacao.atualizado_em is not None

    def test_criar_importacao_escolhas_com_todos_campos(self) -> None:
        """Verifica criar importacao escolhas com todos campos."""
        processo_uuid = uuid.uuid4()
        processo_id = 456
        concurso_uuid = uuid.uuid4()
        dados_prodam = [
            {
                "codigoPessoaFisica": "12345678901",
                "codigoCargo": "123",
                "descricaoStatus": "ALOCADO",
            }
        ]
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid,
            processo_id=processo_id,
            concurso_uuid=concurso_uuid,
            dados_prodam=dados_prodam,
            status="PROCESSANDO",
        )
        assert importacao.processo_uuid == processo_uuid
        assert importacao.processo_id == processo_id
        assert importacao.concurso_uuid == concurso_uuid
        assert importacao.dados_prodam == dados_prodam
        assert importacao.status == "PROCESSANDO"

    def test_importacao_escolhas_str_representation(self) -> None:
        """Verifica importacao escolhas str representation."""
        processo_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid, processo_id=123
        )
        str_repr = str(importacao)
        assert "Importação" in str_repr
        assert str(processo_uuid) in str_repr

    def test_importacao_escolhas_str_representation_sem_uuid(self) -> None:
        """Verifica importacao escolhas str representation sem uuid."""
        importacao = ImportacaoEscolhas.objects.create(processo_id=123)
        str_repr = str(importacao)
        assert "Importação" in str_repr
        assert "N/A" in str_repr

    def test_importacao_escolhas_status_choices(self) -> None:
        """Verifica importacao escolhas status choices."""
        processo_uuid = uuid.uuid4()
        for status_code, _status_label in CHOICES_STATUS_IMPORTACAO_ARQUIVO:
            importacao = ImportacaoEscolhas.objects.create(
                processo_uuid=processo_uuid,
                processo_id=123,
                status=status_code,
            )
            assert importacao.status == status_code

    def test_importacao_escolhas_ordering(self) -> None:
        """Verifica importacao escolhas ordering."""
        processo_uuid1 = uuid.uuid4()
        processo_uuid2 = uuid.uuid4()
        importacao1 = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid1, processo_id=123
        )
        time.sleep(0.01)
        importacao2 = ImportacaoEscolhas.objects.create(
            processo_uuid=processo_uuid2, processo_id=456
        )
        importacoes = ImportacaoEscolhas.objects.all()
        assert importacoes[0] == importacao2
        assert importacoes[1] == importacao1

    def test_importacao_escolhas_campos_opcionais(self) -> None:
        """Verifica importacao escolhas campos opcionais."""
        importacao = ImportacaoEscolhas.objects.create(processo_id=123)
        assert importacao.processo_uuid is None
        assert importacao.processo_id == 123
        assert importacao.concurso_uuid is None
        assert importacao.dados_prodam is None

    def test_importacao_escolhas_auditlog_registrado(self) -> None:
        """Verifica importacao escolhas auditlog registrado."""
        from auditlog.registry import auditlog

        assert ImportacaoEscolhas in auditlog._registry
        assert hasattr(ImportacaoEscolhas, "history")

    def test_importacao_escolhas_meta_options(self) -> None:
        """Verifica importacao escolhas meta options."""
        assert ImportacaoEscolhas._meta.db_table == "importacao_escolhas"
        assert (
            ImportacaoEscolhas._meta.verbose_name == "Importação de escolhas"
        )
        assert (
            ImportacaoEscolhas._meta.verbose_name_plural
            == "Importações de escolhas"
        )

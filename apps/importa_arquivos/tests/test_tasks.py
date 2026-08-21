"""Testes da task de importação de escolhas."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from importa_arquivos.models import ImportacaoEscolhas
from importa_arquivos.tasks import enfileirar_importacoes_escolhas

pytestmark = pytest.mark.django_db


def _agenda_online(processo_uuid: uuid.UUID) -> dict:
    return {
        "processo_convocacao_uuid": str(processo_uuid),
        "modalidade": "ONLINE",
    }


def test_enfileirar_importacoes_escolhas_joga_na_fila() -> None:
    """Enfileira quando há exatamente uma agenda ONLINE."""
    processo_uuid = uuid.uuid4()
    concurso_uuid = uuid.uuid4()
    with (
        patch(
            "importa_arquivos.tasks.ApiProcessosConvocacaoService.listar_pendentes"
        ) as mock_listar,
        patch(
            "importa_arquivos.tasks.ApiAgendasService.buscar_por_processo_convocacao_uuid"
        ) as mock_agendas,
        patch(
            "importa_arquivos.tasks.importar_escolhas.delay"
        ) as mock_delay,
    ):
        mock_listar.return_value = [
            {
                "uuid": str(processo_uuid),
                "concurso_uuid": str(concurso_uuid),
                "processo_id": 123,
            }
        ]
        mock_agendas.return_value = [_agenda_online(processo_uuid)]
        total = enfileirar_importacoes_escolhas()
    assert total == 1
    mock_delay.assert_called_once_with(
        processo_uuid=str(processo_uuid),
        processo_id=123,
        concurso_uuid=str(concurso_uuid),
    )


def test_enfileirar_ignora_quando_agenda_nao_e_unica_online() -> None:
    """Não enfileira se houver mais de uma agenda ou modalidade diferente."""
    processo_uuid = uuid.uuid4()
    concurso_uuid = uuid.uuid4()
    with (
        patch(
            "importa_arquivos.tasks.ApiProcessosConvocacaoService.listar_pendentes"
        ) as mock_listar,
        patch(
            "importa_arquivos.tasks.ApiAgendasService.buscar_por_processo_convocacao_uuid"
        ) as mock_agendas,
        patch(
            "importa_arquivos.tasks.importar_escolhas.delay"
        ) as mock_delay,
    ):
        mock_listar.return_value = [
            {
                "uuid": str(processo_uuid),
                "concurso_uuid": str(concurso_uuid),
                "processo_id": 123,
            }
        ]
        mock_agendas.return_value = [
            _agenda_online(processo_uuid),
            {
                "processo_convocacao_uuid": str(processo_uuid),
                "modalidade": "PRESENCIAL",
            },
        ]
        total = enfileirar_importacoes_escolhas()
    assert total == 0
    mock_delay.assert_not_called()


def test_enfileirar_ignora_processo_ja_concluido() -> None:
    """Não enfileira se já existe ImportacaoEscolhas com sucesso."""
    processo_uuid = uuid.uuid4()
    concurso_uuid = uuid.uuid4()
    ImportacaoEscolhas.objects.create(
        processo_uuid=processo_uuid,
        processo_id=123,
        concurso_uuid=concurso_uuid,
        status="CONCLUIDO",
    )
    with (
        patch(
            "importa_arquivos.tasks.ApiProcessosConvocacaoService.listar_pendentes"
        ) as mock_listar,
        patch(
            "importa_arquivos.tasks.ApiAgendasService.buscar_por_processo_convocacao_uuid"
        ) as mock_agendas,
        patch(
            "importa_arquivos.tasks.importar_escolhas.delay"
        ) as mock_delay,
    ):
        mock_listar.return_value = [
            {
                "uuid": str(processo_uuid),
                "concurso_uuid": str(concurso_uuid),
                "processo_id": 123,
            }
        ]
        total = enfileirar_importacoes_escolhas()
    assert total == 0
    mock_delay.assert_not_called()
    mock_agendas.assert_not_called()


def test_enfileirar_reprocessa_quando_so_existe_erro() -> None:
    """Registro ERRO não bloqueia novo enfileiramento."""
    processo_uuid = uuid.uuid4()
    concurso_uuid = uuid.uuid4()
    ImportacaoEscolhas.objects.create(
        processo_uuid=processo_uuid,
        processo_id=123,
        concurso_uuid=concurso_uuid,
        status="ERRO",
    )
    with (
        patch(
            "importa_arquivos.tasks.ApiProcessosConvocacaoService.listar_pendentes"
        ) as mock_listar,
        patch(
            "importa_arquivos.tasks.ApiAgendasService.buscar_por_processo_convocacao_uuid"
        ) as mock_agendas,
        patch(
            "importa_arquivos.tasks.importar_escolhas.delay"
        ) as mock_delay,
    ):
        mock_listar.return_value = [
            {
                "uuid": str(processo_uuid),
                "concurso_uuid": str(concurso_uuid),
                "processo_id": 123,
            }
        ]
        mock_agendas.return_value = [_agenda_online(processo_uuid)]
        total = enfileirar_importacoes_escolhas()
    assert total == 1
    mock_delay.assert_called_once()


def test_enfileirar_importacoes_escolhas_sem_registros() -> None:
    """Sem processos pendentes, o Beat não enfileira nada."""
    with (
        patch(
            "importa_arquivos.tasks.ApiProcessosConvocacaoService.listar_pendentes"
        ) as mock_listar,
        patch(
            "importa_arquivos.tasks.importar_escolhas.delay"
        ) as mock_delay,
    ):
        mock_listar.return_value = []
        total = enfileirar_importacoes_escolhas()
    assert total == 0
    mock_delay.assert_not_called()

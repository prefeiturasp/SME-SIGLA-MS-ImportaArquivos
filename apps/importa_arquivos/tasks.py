"""Tasks de importação de arquivos."""

from __future__ import annotations

import logging
from typing import Any

from importa_arquivos.models.constants import MODO_IMPORTACAO_AUTOMATICA
from importa_arquivos.repository import ImportacaoEscolhasRepository
from importa_arquivos.services.api_agendas import ApiAgendasService
from importa_arquivos.services.api_processos_convocacao import (
    ApiProcessosConvocacaoService,
)
from importa_arquivos.services.importacao_escolhas_service import (
    ImportacaoEscolhasService,
)

from config.celery import app

logger = logging.getLogger(__name__)


def agenda_unica_online(agendas: list[dict[str, Any]]) -> bool:
    """Indica se há exatamente uma agenda com modalidade ONLINE.

    Args:
        agendas: Lista de agendas retornada pelo MS-Agenda.

    Returns:
        ``True`` quando a lista tem um único item ONLINE.
    """
    if len(agendas) != 1:
        return False
    modalidade = (agendas[0].get("modalidade") or "").upper()
    return modalidade == "ONLINE"


@app.task(name="importa_arquivos.tasks.importar_escolhas")
def importar_escolhas(
    processo_uuid: Any,
    processo_id: Any,
    concurso_uuid: Any,
) -> str:
    """Executa a importação de escolhas via service (consumida pelo worker).

    Args:
        processo_uuid: UUID do processo de convocação.
        processo_id: Identificador numérico usado na API PRODAM.
        concurso_uuid: UUID do concurso.

    Returns:
        UUID da ``ImportacaoEscolhas`` processada, em string.
    """
    logger.info(
        "Iniciando task de importação de escolhas: "
        f"processo_uuid={processo_uuid} processo_id={processo_id}"
    )
    instance = ImportacaoEscolhasService.processar(
        processo_uuid=processo_uuid,
        processo_id=processo_id,
        concurso_uuid=concurso_uuid,
        modo=MODO_IMPORTACAO_AUTOMATICA,
    )
    return str(instance.uuid)


@app.task(name="importa_arquivos.tasks.enfileirar_importacoes_escolhas")
def enfileirar_importacoes_escolhas() -> int:
    """Enfileira ``importar_escolhas`` para processos pendentes.

    Chamada pelo Celery Beat: consulta o MS-Processos, descarta os que
    já tiveram importação concluída e joga o restante na fila quando a
    agenda for única e ONLINE.

    Returns:
        Quantidade de tasks enfileiradas.
    """
    logger.info("Enfileirando importações de escolhas")
    service = ApiProcessosConvocacaoService()
    agendas_service = ApiAgendasService()
    processos_brutos = service.listar_pendentes()
    processos = service.extrair_processo_uuid_e_id(processos_brutos)
    enfileiradas = 0
    for item in processos:
        processo_uuid = item["processo_uuid"]
        processo_id = item["processo_id"]
        concurso_uuid = item["concurso_uuid"]
        if ImportacaoEscolhasRepository.existe_sucesso(
            processo_uuid=processo_uuid,
            processo_id=processo_id,
        ):
            logger.info(
                "Processo já importado com sucesso, ignorado: "
                f"processo_uuid={processo_uuid} processo_id={processo_id}"
            )
            continue

        agendas = agendas_service.buscar_por_processo_convocacao_uuid(
            processo_uuid
        )
        if not agenda_unica_online(agendas):
            logger.info(
                "Agenda não elegível para importação automática: "
                f"processo_uuid={processo_uuid} qtd_agendas={len(agendas)}"
            )
            continue

        importar_escolhas.delay(
            processo_uuid=str(processo_uuid),
            processo_id=processo_id,
            concurso_uuid=str(concurso_uuid),
        )
        enfileiradas += 1
        logger.info(
            "Task importar_escolhas enfileirada: "
            f"processo_uuid={processo_uuid} processo_id={processo_id}"
        )
    logger.info("%s importações de escolhas enfileiradas", enfileiradas)
    return enfileiradas

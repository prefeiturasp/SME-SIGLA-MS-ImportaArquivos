"""Serviço de exportação de lotes (formato ERGON/SIGPEC).

Fluxo:
1. Busca todos os ConcursoCandidato do lote via MS-Candidatos.
2. Busca as Escolhas dos candidatos via MS-Escolhas, filtrando por
concurso_uuid.
3. Valida que todos os candidatos têm escolha. Se não →
ExportacaoLoteIncompletaException.
4. Gera o arquivo: cabeçalho configurável + linhas de dados.

Formato de cada linha:
    {numero_lote};{codigo_sigpec};{chave_inscrito};{DDMMYYYY};{S|R};{codigo_integracao};
"""

import logging
from datetime import datetime
from typing import Any

from exporta_arquivo.models import ExportacaoLote
from exporta_arquivo.services.api_candidatos import ApiCandidatosService
from exporta_arquivo.services.api_escolhas import ApiEscolhasService
from exporta_arquivo.services.exceptions import (
    ExportacaoLoteIncompletaException,
)

logger = logging.getLogger(__name__)


def _data_para_ddmmyyyy(val: Any) -> str:
    """Executa  data para ddmmyyyy.

    Args:
        val: Parâmetro val.

    Returns:
        Texto resultante da operação.

    Raises:
        Nenhuma exceção específica documentada.
    """
    try:
        data_obj = datetime.fromisoformat(val.replace("Z", "+00:00"))
    except ValueError:
        data_obj = datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f %z")
    return data_obj.strftime("%d%m%Y")


def gerar_conteudo_lote(
    candidatos: list[dict[str, Any]],
    escolhas_por_candidato: dict[str, dict[str, Any]],
) -> str:
    """Gera o conteúdo completo do arquivo de exportação de lotes.

    Args:
        candidatos: Parâmetro candidatos.
        escolhas_por_candidato: Parâmetro escolhas por candidato.

    Returns:
        Texto resultante da operação.

    Raises:
        Nenhuma exceção específica documentada.
    """
    cabecalho = """@TABELA=[c_ERGON][PMSP_ESCOLHA_VAGA_SME][1.0]
        @CHAVE=[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER]
        @TAG INICIO=
        @TAG FIM=
        @SEPARADOR=;
        @FORMATO DATA=DD/MM/YYYY
        @COLUNAS=[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER][DATA_ESCOLHA][DATE][ESCOLHEU_VAGA][VARCHAR2][SETOR][VARCHAR2]"""

    linhas: list[str] = [cabecalho]

    for candidato in candidatos:
        candidato_uuid = str(
            candidato.get("uuid")
            or candidato.get("concurso_candidato_uuid")
            or ""
        )
        candidato_data = candidato.get("candidato") or {}
        candidato_uuid_real = str(candidato_data.get("uuid") or "")

        escolha = (
            escolhas_por_candidato.get(candidato_uuid_real)
            or escolhas_por_candidato.get(candidato_uuid)
            or {}
        )

        numero_lote = candidato.get("numero_lote")
        codigo_sigpec = candidato.get("codigo_sigpec")
        chave_inscrito = candidato.get("chave_inscrito")

        criado_em = escolha.get("criado_em")
        data_escolha = _data_para_ddmmyyyy(criado_em) if criado_em else ""

        situacao = escolha.get("situacao")
        mapa_escolheu = {
            "escolha": "S",
            "nao-escolha": "N",
            "reconvocacao": "R",
        }
        escolheu = mapa_escolheu.get(situacao, "R")  # type: ignore[arg-type]
        codigo_integracao = ""

        if situacao == "escolha":
            vaga_escola = escolha.get("vaga_escola") or {}
            escola = (
                vaga_escola.get("escola")
                if isinstance(vaga_escola, dict)
                else {}
            )
            escola = escola or {}
            codigo_integracao = escola.get("codigo_integracao") or ""

        if situacao not in mapa_escolheu:
            logger.warning(
                "Situacao inesperada na exportacao de lote: candidato_uuid=%s situacao=%s",  # noqa: E501
                candidato_uuid or candidato_uuid_real,
                situacao,
            )

        linha = f"{numero_lote};{codigo_sigpec};{chave_inscrito};{data_escolha};{escolheu};{codigo_integracao};"  # noqa: E501
        linhas.append(linha)

    return "\n".join(linhas) + "\n"


def exportar_lote(instance: ExportacaoLote) -> str:
    """Orquestra a exportação de um lote:.

    Args:
        instance: Instância do modelo em atualização.

    Returns:
        Texto resultante da operação.

    Raises:
        ExportacaoLoteIncompletaException: Se ocorrer erro nesta operação.
    """
    # 1. Buscar candidatos do lote
    # Usa numero_lote quando disponível (novos registros); fallback para lote_uuid (registros antigos)  # noqa: E501

    candidatos = ApiCandidatosService().get_habilitados(
        concurso_uuid=str(instance.concurso_uuid),
        numero_lote=instance.numero_lote,
    )

    # 2. Extrair UUIDs dos candidatos (ConcursoCandidato.uuid — chave usada pelo sistema de escolhas)  # noqa: E501
    candidato_uuids: list[str] = []
    for c in candidatos:
        uuid_val = str(c.get("uuid") or c.get("concurso_candidato_uuid") or "")
        if uuid_val:
            candidato_uuids.append(uuid_val)

    # 3. Buscar escolhas filtradas por concurso_uuid
    escolhas_lista = ApiEscolhasService().get_escolhas(
        candidato_uuids=candidato_uuids,
        concurso_uuid=str(instance.concurso_uuid),
    )

    # 4. Mapear escolhas por candidato_uuid
    escolhas_por_candidato: dict[str, dict[str, Any]] = {}
    for escolha in escolhas_lista:
        cand_uuid = str(escolha.get("candidato_uuid") or "")
        if cand_uuid:  # noqa: SIM102
            # Mantém a mais recente (lista já vem ordenada por -criado_em da API)  # noqa: E501
            if cand_uuid not in escolhas_por_candidato:
                escolhas_por_candidato[cand_uuid] = escolha

    # 5. Validar: todos os candidatos devem ter escolha
    sem_escolha: list[str] = []
    for candidato in candidatos:
        candidato_data = candidato.get("candidato") or {}
        uuid_val = str(
            candidato.get("uuid")
            or candidato.get("concurso_candidato_uuid")
            or ""
        )
        if uuid_val not in escolhas_por_candidato:
            nome = candidato_data.get("nome") or uuid_val
            sem_escolha.append(nome)

    if sem_escolha:
        raise ExportacaoLoteIncompletaException(
            candidatos_sem_escolha=sem_escolha
        )

    # 6. Gerar arquivo
    return gerar_conteudo_lote(candidatos, escolhas_por_candidato)

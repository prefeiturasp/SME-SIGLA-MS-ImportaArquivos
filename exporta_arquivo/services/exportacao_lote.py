"""
Serviço de exportação de lotes (formato ERGON/SIGPEC).

Fluxo:
1. Busca todos os ConcursoCandidato do lote via MS-Candidatos.
2. Busca as Escolhas dos candidatos via MS-Escolhas, filtrando por concurso_uuid.
3. Valida que todos os candidatos têm escolha. Se não → ExportacaoLoteIncompletaException.
4. Gera o arquivo: cabeçalho configurável + linhas de dados.

Formato de cada linha:
    {numero_lote};{codigo_sigpec};{chave_inscrito};{DDMMYYYY};{S|R};{codigo_integracao};
"""
import logging
from typing import Any, Dict, List, Optional

from exporta_arquivo.models import ExportacaoLote, CabecalhoExportacaoLote
from exporta_arquivo.services.api_lote import ApiLoteCandidatosService, ApiLoteEscolhasService

logger = logging.getLogger(__name__)


class ExportacaoLoteIncompletaException(Exception):
    """
    Levantada quando nem todos os candidatos do lote realizaram escolha.
    Carrega a lista de nomes de candidatos sem escolha.
    """

    def __init__(self, candidatos_sem_escolha: List[str]):
        self.candidatos_sem_escolha = candidatos_sem_escolha
        super().__init__(
            f"{len(candidatos_sem_escolha)} candidato(s) sem escolha no lote."
        )


def _data_para_ddmmyyyy(val: Any) -> str:
    """Converte data ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM...) para DDMMYYYY."""
    if not val:
        return ""
    s = str(val).strip()
    if "T" in s:
        s = s.split("T")[0]
    if "-" in s:
        partes = s.split("-")
        if len(partes) == 3:
            return f"{partes[2]}{partes[1]}{partes[0]}"
    return s


def _campo(val: Any, sep: str = ";") -> str:
    """Normaliza valor para o arquivo (sem quebras de linha, sem separador no conteúdo)."""
    if val is None:
        return ""
    s = str(val).strip().replace("\r", " ").replace("\n", " ")
    return s.replace(sep, " ") if sep in s else s


def gerar_arquivo_lote(
    candidatos: List[Dict[str, Any]],
    escolhas_por_candidato: Dict[str, Dict[str, Any]],
    cabecalho: CabecalhoExportacaoLote,
) -> str:
    """
    Gera o conteúdo completo do arquivo de exportação de lotes.

    Cada linha segue o padrão:
        {numero_lote};{codigo_sigpec};{chave_inscrito};{DDMMYYYY};{S|R};{codigo_integracao};

    Retorna string com cabeçalho + linhas de dados.
    """
    sep = cabecalho.separador
    linhas: List[str] = [cabecalho.render()]

    for candidato in candidatos:
        candidato_uuid = str(candidato.get("uuid") or candidato.get("concurso_candidato_uuid") or "")
        # Tenta obter pelo UUID do candidato (candidato.candidato.uuid ou candidato_uuid do campo)
        candidato_data = candidato.get("candidato") or {}
        candidato_uuid_real = str(candidato_data.get("uuid") or "")

        escolha = escolhas_por_candidato.get(candidato_uuid_real) or escolhas_por_candidato.get(candidato_uuid)

        numero_lote = _campo(candidato.get("numero_lote"), sep)
        codigo_sigpec = _campo(candidato.get("codigo_sigpec"), sep)
        chave_inscrito = _campo(candidato.get("chave_inscrito"), sep)

        if escolha:
            data_escolha = _data_para_ddmmyyyy(escolha.get("criado_em"))
            vaga_escola = escolha.get("vaga_escola") or {}
            escola = (vaga_escola.get("escola") or {}) if isinstance(vaga_escola, dict) else {}
            codigo_integracao = _campo(escola.get("codigo_integracao"), sep)
            escolheu = "S" if codigo_integracao else "R"
        else:
            data_escolha = ""
            escolheu = "R"
            codigo_integracao = ""

        linha = (
            f"{numero_lote}{sep}"
            f"{codigo_sigpec}{sep}"
            f"{chave_inscrito}{sep}"
            f"{data_escolha}{sep}"
            f"{escolheu}{sep}"
            f"{codigo_integracao}{sep}"
        )
        linhas.append(linha)

    return "\n".join(linhas) + "\n"


def exportar_lote(instance: ExportacaoLote) -> str:
    """
    Orquestra a exportação de um lote:
    1. Busca candidatos do lote.
    2. Busca escolhas dos candidatos para o concurso.
    3. Valida que todos têm escolha (levanta ExportacaoLoteIncompletaException se não).
    4. Gera e retorna o conteúdo do arquivo.
    """
    candidatos_service = ApiLoteCandidatosService()
    escolhas_service = ApiLoteEscolhasService()

    # 1. Buscar candidatos do lote
    candidatos = candidatos_service.get_candidatos_lote(str(instance.lote_uuid))

    if not candidatos:
        raise ExportacaoLoteIncompletaException(candidatos_sem_escolha=[])

    # 2. Extrair UUIDs dos candidatos (campo candidato.uuid)
    candidato_uuids: List[str] = []
    for c in candidatos:
        candidato_data = c.get("candidato") or {}
        uuid_val = str(candidato_data.get("uuid") or "")
        if uuid_val:
            candidato_uuids.append(uuid_val)

    # 3. Buscar escolhas filtradas por concurso_uuid
    escolhas_raw = escolhas_service.get_escolhas_lote(
        candidato_uuids=candidato_uuids,
        concurso_uuid=str(instance.concurso_uuid),
    )

    # 4. Mapear escolhas por candidato_uuid
    escolhas_por_candidato: Dict[str, Dict[str, Any]] = {}
    for escolha in escolhas_raw:
        cand_uuid = str(escolha.get("candidato_uuid") or "")
        if cand_uuid:
            # Mantém a mais recente (lista já vem ordenada por -criado_em da API)
            if cand_uuid not in escolhas_por_candidato:
                escolhas_por_candidato[cand_uuid] = escolha

    # 5. Validar: todos os candidatos devem ter escolha
    sem_escolha: List[str] = []
    for candidato in candidatos:
        candidato_data = candidato.get("candidato") or {}
        uuid_val = str(candidato_data.get("uuid") or "")
        if uuid_val not in escolhas_por_candidato:
            nome = candidato_data.get("nome") or uuid_val
            sem_escolha.append(nome)

    if sem_escolha:
        raise ExportacaoLoteIncompletaException(candidatos_sem_escolha=sem_escolha)

    # 6. Obter cabeçalho ativo
    cabecalho = CabecalhoExportacaoLote.objects.filter(ativo=True).first()
    if not cabecalho:
        # Fallback: cabeçalho padrão em memória se não houver registro
        cabecalho = CabecalhoExportacaoLote()

    # 7. Gerar arquivo
    return gerar_arquivo_lote(candidatos, escolhas_por_candidato, cabecalho)

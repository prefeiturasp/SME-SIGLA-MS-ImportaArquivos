"""Testes do serviço exportacao_lote.py:.

- _data_para_ddmmyyyy: formatos ISO e legado
- gerar_conteudo_lote: cabeçalho, linhas escolha/recusa, lookup por uuid
- exportar_lote: orquestração (mocks de ApiCandidatosService e
ApiEscolhasService)
Sem HTTP/DB.
"""

from __future__ import annotations

import contextlib
import uuid
from typing import Any
from unittest.mock import patch

import pytest

from exporta_arquivo.services.exceptions import (
    ExportacaoLoteIncompletaException,
)
from exporta_arquivo.services.exportacao_lote import (
    _data_para_ddmmyyyy,
    exportar_lote,
    gerar_conteudo_lote,
)


def _uuid() -> Any:
    """Uuid."""
    return str(uuid.uuid4())


def _candidato(
    cand_uuid: Any = None,
    numero_lote: Any = 1,
    codigo_sigpec: Any = "SIG001",
    chave_inscrito: Any = "123",
    nome: Any = "João",
) -> Any:
    """Candidato."""
    cand_uuid = cand_uuid or _uuid()
    return {
        "uuid": cand_uuid,
        "numero_lote": numero_lote,
        "codigo_sigpec": codigo_sigpec,
        "chave_inscrito": chave_inscrito,
        "candidato": {"uuid": cand_uuid, "nome": nome},
    }


def _escolha(
    candidato_uuid: Any,
    situacao: Any = "escolha",
    codigo_integracao: Any = "ESCOLA01",
) -> Any:
    """Escolha."""
    return {
        "candidato_uuid": candidato_uuid,
        "situacao": situacao,
        "criado_em": "2024-06-15T10:00:00Z",
        "vaga_escola": {"escola": {"codigo_integracao": codigo_integracao}},
    }


def _recusa(candidato_uuid: Any) -> Any:
    """Recusa."""
    return {
        "candidato_uuid": candidato_uuid,
        "situacao": "recusa",
        "criado_em": "2024-06-15T10:00:00Z",
        "vaga_escola": None,
    }


class TestDataParaDdmmyyyy:
    """Converte datas em diferentes formatos para DDMMYYYY."""

    def test_iso_com_z(self) -> None:
        """Verifica iso com z."""
        assert _data_para_ddmmyyyy("2024-01-15T00:00:00Z") == "15012024"

    def test_iso_com_offset_positivo(self) -> None:
        """Verifica iso com offset positivo."""
        assert _data_para_ddmmyyyy("2024-06-30T23:59:59+03:00") == "30062024"

    def test_iso_com_offset_negativo(self) -> None:
        """Verifica iso com offset negativo."""
        assert _data_para_ddmmyyyy("2024-12-01T12:00:00-05:00") == "01122024"

    def test_formato_legado_com_microsegundos(self) -> None:
        """Verifica formato legado com microsegundos."""
        assert (
            _data_para_ddmmyyyy("2024-03-07 08:30:00.000000 +0000")
            == "07032024"
        )

    def test_dia_e_mes_com_zero_a_esquerda(self) -> None:
        """Verifica dia e mes com zero a esquerda."""
        assert _data_para_ddmmyyyy("2024-05-03T00:00:00Z") == "03052024"


class TestGerarConteudoLote:
    """Cabeçalho ERGON + linhas no formato."""

    def test_cabecalho_ergon_presente(self) -> None:
        """Verifica cabecalho ergon presente."""
        out = gerar_conteudo_lote([], {})
        assert "@TABELA=" in out
        assert "@SEPARADOR=;" in out
        assert "@COLUNAS=" in out

    def test_arquivo_termina_com_newline(self) -> None:
        """Verifica arquivo termina com newline."""
        out = gerar_conteudo_lote([], {})
        assert out.endswith("\n")

    def test_lista_vazia_retorna_so_cabecalho(self) -> None:
        """Verifica lista vazia retorna so cabecalho."""
        out = gerar_conteudo_lote([], {})
        linhas_dados = [
            l
            for l in out.strip().split("\n")
            if not l.strip().startswith("@") and l.strip()
        ]
        assert linhas_dados == []

    def test_escolha_gera_linha_com_s_e_codigo_integracao(self) -> None:
        """Verifica escolha gera linha com s e codigo integracao."""
        cand_uuid = _uuid()
        candidato = _candidato(
            cand_uuid=cand_uuid,
            numero_lote=5,
            codigo_sigpec="SIG99",
            chave_inscrito="777",
        )
        escolha = _escolha(
            cand_uuid, situacao="escolha", codigo_integracao="SETOR42"
        )
        out = gerar_conteudo_lote([candidato], {cand_uuid: escolha})
        assert "5;SIG99;777;" in out
        assert ";S;SETOR42;" in out

    def test_recusa_gera_linha_com_r_e_sem_codigo_integracao(self) -> None:
        """Verifica recusa gera linha com r e sem codigo integracao."""
        cand_uuid = _uuid()
        candidato = _candidato(
            cand_uuid=cand_uuid,
            numero_lote=2,
            codigo_sigpec="SIG01",
            chave_inscrito="100",
        )
        recusa = _recusa(cand_uuid)
        out = gerar_conteudo_lote([candidato], {cand_uuid: recusa})
        assert ";R;;" in out

    def test_data_escolha_formatada_ddmmyyyy(self) -> None:
        """Verifica data escolha formatada ddmmyyyy."""
        cand_uuid = _uuid()
        candidato = _candidato(cand_uuid=cand_uuid)
        escolha = {
            "candidato_uuid": cand_uuid,
            "situacao": "escolha",
            "criado_em": "2024-08-20T00:00:00Z",
            "vaga_escola": {"escola": {"codigo_integracao": "X"}},
        }
        out = gerar_conteudo_lote([candidato], {cand_uuid: escolha})
        assert "20082024" in out

    def test_varios_candidatos_geram_varias_linhas(self) -> None:
        """Verifica varios candidatos geram varias linhas."""
        c1, c2 = (_uuid(), _uuid())
        candidatos = [
            _candidato(
                cand_uuid=c1,
                numero_lote=1,
                codigo_sigpec="SIG1",
                chave_inscrito="1",
            ),
            _candidato(
                cand_uuid=c2,
                numero_lote=1,
                codigo_sigpec="SIG2",
                chave_inscrito="2",
            ),
        ]
        escolhas = {
            c1: _escolha(c1, codigo_integracao="A"),
            c2: _escolha(c2, codigo_integracao="B"),
        }
        out = gerar_conteudo_lote(candidatos, escolhas)
        assert ";A;" in out
        assert ";B;" in out

    def test_lookup_por_uuid_do_campo_candidato(self) -> None:
        """Verifica lookup por uuid do campo candidato."""
        inner_uuid = _uuid()
        outer_uuid = _uuid()
        candidato = {
            "uuid": outer_uuid,
            "numero_lote": 3,
            "codigo_sigpec": "X",
            "chave_inscrito": "9",
            "candidato": {"uuid": inner_uuid, "nome": "Ana"},
        }
        escolha = _escolha(inner_uuid, codigo_integracao="INNR")
        out = gerar_conteudo_lote([candidato], {inner_uuid: escolha})
        assert ";S;INNR;" in out

    def test_lookup_fallback_por_uuid_externo(self) -> None:
        """Verifica lookup fallback por uuid externo."""
        outer_uuid = _uuid()
        candidato = {
            "uuid": outer_uuid,
            "numero_lote": 1,
            "codigo_sigpec": "Y",
            "chave_inscrito": "8",
            "candidato": {},
        }
        escolha = _escolha(outer_uuid, codigo_integracao="OUTR")
        out = gerar_conteudo_lote([candidato], {outer_uuid: escolha})
        assert ";S;OUTR;" in out


@pytest.mark.django_db
class TestExportarLote:
    """Orquestração: busca candidatos → escolhas → valida → gera conteúdo."""

    @pytest.fixture
    def instance(self) -> Any:
        """Instance."""
        from exporta_arquivo.models import ExportacaoLote

        return ExportacaoLote.objects.create(
            concurso_uuid=uuid.uuid4(),
            concurso_nome="Concurso Teste",
            numero_lote=1,
            lote_uuid=uuid.uuid4(),
        )

    def test_sucesso_retorna_conteudo_com_cabecalho(
        self, instance: Any
    ) -> None:
        """Verifica sucesso retorna conteudo com cabecalho."""
        cand_uuid = _uuid()
        candidatos = [_candidato(cand_uuid=cand_uuid)]
        escolhas = [_escolha(cand_uuid, codigo_integracao="SCL01")]
        with (
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiCandidatosService"
            ) as MockCand,
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiEscolhasService"
            ) as MockEsc,
        ):
            MockCand.return_value.get_habilitados.return_value = candidatos
            MockEsc.return_value.get_escolhas.return_value = escolhas
            resultado = exportar_lote(instance)
        assert "@TABELA=" in resultado
        assert ";S;SCL01;" in resultado

    def test_chama_candidatos_com_concurso_uuid_e_numero_lote(
        self, instance: Any
    ) -> None:
        """Verifica chama candidatos com concurso uuid e numero lote."""
        cand_uuid = _uuid()
        candidatos = [_candidato(cand_uuid=cand_uuid)]
        with (
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiCandidatosService"
            ) as MockCand,
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiEscolhasService"
            ) as MockEsc,
        ):
            MockCand.return_value.get_habilitados.return_value = candidatos
            MockEsc.return_value.get_escolhas.return_value = [
                _escolha(cand_uuid)
            ]
            exportar_lote(instance)
        MockCand.return_value.get_habilitados.assert_called_once_with(
            concurso_uuid=str(instance.concurso_uuid),
            numero_lote=instance.numero_lote,
        )

    def test_chama_escolhas_com_candidato_uuids_e_concurso_uuid(
        self, instance: Any
    ) -> None:
        """Verifica chama escolhas com candidato uuids e concurso uuid."""
        cand_uuid = _uuid()
        candidatos = [_candidato(cand_uuid=cand_uuid)]
        with (
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiCandidatosService"
            ) as MockCand,
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiEscolhasService"
            ) as MockEsc,
        ):
            MockCand.return_value.get_habilitados.return_value = candidatos
            MockEsc.return_value.get_escolhas.return_value = [
                _escolha(cand_uuid)
            ]
            exportar_lote(instance)
        MockEsc.return_value.get_escolhas.assert_called_once_with(
            candidato_uuids=[cand_uuid],
            concurso_uuid=str(instance.concurso_uuid),
        )

    def test_candidato_sem_escolha_levanta_incompleta(
        self, instance: Any
    ) -> None:
        """Verifica candidato sem escolha levanta incompleta."""
        cand_uuid = _uuid()
        candidatos = [_candidato(cand_uuid=cand_uuid, nome="Maria")]
        with (
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiCandidatosService"
            ) as MockCand,
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiEscolhasService"
            ) as MockEsc,
        ):
            MockCand.return_value.get_habilitados.return_value = candidatos
            MockEsc.return_value.get_escolhas.return_value = []
            with pytest.raises(ExportacaoLoteIncompletaException) as exc_info:
                exportar_lote(instance)
        assert "Maria" in exc_info.value.candidatos_sem_escolha

    def test_candidato_sem_uuid_nao_incluido_na_lista_enviada_a_api_escolhas(
        self, instance: Any
    ) -> None:
        """Verifica candidato sem uuid nao incluido na lista enviada a api escolhas."""
        cand_uuid = _uuid()
        candidatos = [
            {
                "uuid": "",
                "concurso_candidato_uuid": "",
                "numero_lote": 1,
                "codigo_sigpec": "X",
                "chave_inscrito": "1",
                "candidato": {},
            },
            _candidato(cand_uuid=cand_uuid),
        ]
        with (
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiCandidatosService"
            ) as MockCand,
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiEscolhasService"
            ) as MockEsc,
        ):
            MockCand.return_value.get_habilitados.return_value = candidatos
            MockEsc.return_value.get_escolhas.return_value = [
                _escolha(cand_uuid)
            ]
            with contextlib.suppress(ExportacaoLoteIncompletaException):
                exportar_lote(instance)
        chamada = MockEsc.return_value.get_escolhas.call_args
        uuids_enviados = chamada.kwargs.get("candidato_uuids") or chamada[
            1
        ].get("candidato_uuids", [])
        assert "" not in uuids_enviados
        assert cand_uuid in uuids_enviados

    def test_primeira_escolha_por_candidato_prevalece(
        self, instance: Any
    ) -> None:
        """Verifica primeira escolha por candidato prevalece."""
        cand_uuid = _uuid()
        candidatos = [_candidato(cand_uuid=cand_uuid)]
        escolha_recente = {
            "candidato_uuid": cand_uuid,
            "situacao": "escolha",
            "criado_em": "2024-09-01T00:00:00Z",
            "vaga_escola": {"escola": {"codigo_integracao": "FIRST"}},
        }
        escolha_antiga = {
            "candidato_uuid": cand_uuid,
            "situacao": "recusa",
            "criado_em": "2024-08-01T00:00:00Z",
            "vaga_escola": None,
        }
        with (
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiCandidatosService"
            ) as MockCand,
            patch(
                "exporta_arquivo.services.exportacao_lote.ApiEscolhasService"
            ) as MockEsc,
        ):
            MockCand.return_value.get_habilitados.return_value = candidatos
            MockEsc.return_value.get_escolhas.return_value = [
                escolha_recente,
                escolha_antiga,
            ]
            resultado = exportar_lote(instance)
        assert ";S;FIRST;" in resultado
        assert ";R;;" not in resultado

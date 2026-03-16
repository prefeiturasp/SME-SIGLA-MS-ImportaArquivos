"""
Testes de formatação e orquestração do serviço exportacao_vagas_sigpec.
formatar_arquivo_sigpec + buscar_vagas_escolas (mock de ApiEscolhasService).
Sem HTTP/DB.
"""
from unittest.mock import MagicMock, patch

import pytest

from exporta_arquivo.services.exportacao_vagas_sigpec import (
    SIGPEC_HEADER_LINES,
    buscar_vagas_escolas,
    formatar_arquivo_sigpec,
)


class TestFormatarArquivoSigpec:
    """Cabeçalho fixo + linhas codigo_integracao;v_def;v_prec;"""

    def test_cabecalho_fixo_presente(self):
        out = formatar_arquivo_sigpec([])
        for line in SIGPEC_HEADER_LINES:
            assert line in out
        assert out.startswith("@TABELA=")

    def test_lista_vazia_so_cabecalho(self):
        out = formatar_arquivo_sigpec([])
        linhas = out.strip().split("\n")
        assert len(linhas) == len(SIGPEC_HEADER_LINES)
        assert out.endswith("\n")

    def test_uma_linha_formato_sigpec(self):
        vagas = [
            {
                "codigo_integracao": "SETOR001",
                "vagas_definitivas": 3,
                "vagas_precarias": 1,
            }
        ]
        out = formatar_arquivo_sigpec(vagas)
        assert "SETOR001;3;1;" in out
        linhas = out.strip().split("\n")
        assert len(linhas) == len(SIGPEC_HEADER_LINES) + 1

    def test_varias_linhas(self):
        vagas = [
            {"codigo_integracao": "A", "vagas_definitivas": 1, "vagas_precarias": 0},
            {"codigo_integracao": "B", "vagas_definitivas": 0, "vagas_precarias": 2},
        ]
        out = formatar_arquivo_sigpec(vagas)
        assert "A;1;0;" in out
        assert "B;0;2;" in out
        linhas = out.strip().split("\n")
        assert len(linhas) == len(SIGPEC_HEADER_LINES) + 2

    def test_separador_ponto_virgula(self):
        vagas = [{"codigo_integracao": "X", "vagas_definitivas": 0, "vagas_precarias": 0}]
        out = formatar_arquivo_sigpec(vagas)
        assert "X;0;0;" in out


class TestBuscarVagasEscolasSigpec:
    """buscar_vagas_escolas com mock de ApiEscolhasService.get_vagas_escolas."""

    def test_payload_valido_retorna_lista_com_codigo_integracao_e_vagas(self):
        payload_valido = {
            "vagas": [
                {
                    "vagas_definitivas": 3,
                    "vagas_precarias": 1,
                    "escola": {"codigo_integracao": "SETOR001", "codigo_eol": "123"},
                    "cargo_codigo": 100,
                },
            ],
        }
        mock_api = MagicMock()
        mock_api.get_vagas_escolas.return_value = payload_valido
        with patch(
            "exporta_arquivo.services.exportacao_vagas_sigpec.ApiEscolhasService",
            return_value=mock_api,
        ):
            resultado = buscar_vagas_escolas("processo-uuid", 100)
        assert len(resultado) == 1
        assert resultado[0]["codigo_integracao"] == "SETOR001"
        assert resultado[0]["vagas_definitivas"] == 3
        assert resultado[0]["vagas_precarias"] == 1
        mock_api.get_vagas_escolas.assert_called_once_with("processo-uuid", 100)

    def test_payload_invalido_serializer_levanta_erro(self):
        from rest_framework.exceptions import ValidationError

        payload_invalido = {"vagas": []}
        mock_api = MagicMock()
        mock_api.get_vagas_escolas.return_value = payload_invalido
        with patch(
            "exporta_arquivo.services.exportacao_vagas_sigpec.ApiEscolhasService",
            return_value=mock_api,
        ):
            with pytest.raises(ValidationError):
                buscar_vagas_escolas("processo-uuid", 100)

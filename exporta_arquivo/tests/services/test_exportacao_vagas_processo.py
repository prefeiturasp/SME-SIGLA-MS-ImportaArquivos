"""
Testes de formatação e orquestração do serviço exportacao_vagas_processo.
formatar_arquivo_vagas_processo + buscar_vagas_escolas (mock de
ApiEscolhasService).
Sem HTTP/DB.
"""

from unittest.mock import MagicMock, patch

import pytest

from exporta_arquivo.services.exportacao_vagas_processo import (
    buscar_vagas_escolas,
    formatar_arquivo_vagas_processo,
)


class TestFormatarArquivoVagasProcesso:
    """
    Formato esperado: codigo_cargo|codigo_eol|v_def|v_prec por linha, sem
    cabeçalho.
    """

    def test_lista_vazia_retorna_string_vazia(self):
        assert formatar_arquivo_vagas_processo(1001, []) == ""

    def test_uma_linha_formato_correto(self):
        linhas = [
            {
                "codigo_eol": "123456",
                "vagas_definitivas": 2,
                "vagas_precarias": 1,
            }
        ]
        out = formatar_arquivo_vagas_processo(1001, linhas)
        assert out == "1001|123456|2|1\n"
        assert out.endswith("\n")

    def test_varias_linhas(self):
        linhas = [
            {
                "codigo_eol": "EOL1",
                "vagas_definitivas": 1,
                "vagas_precarias": 0,
            },
            {
                "codigo_eol": "EOL2",
                "vagas_definitivas": 0,
                "vagas_precarias": 2,
            },
        ]
        out = formatar_arquivo_vagas_processo(500, linhas)
        assert out == "500|EOL1|1|0\n500|EOL2|0|2\n"
        assert out.count("\n") == 2

    def test_valores_default_zero(self):
        linhas = [
            {
                "codigo_eol": "X",
                "vagas_definitivas": None,
                "vagas_precarias": None,
            }
        ]
        out = formatar_arquivo_vagas_processo(1, linhas)
        assert "1|X|0|0" in out


class TestBuscarVagasEscolasVagasProcesso:
    """
    buscar_vagas_escolas com mock de ApiEscolhasService.get_vagas_escolas.
    """

    def test_payload_valido_retorna_lista_com_codigo_eol_e_vagas(self):
        payload_valido = {
            "vagas": [
                {
                    "vagas_definitivas": 2,
                    "vagas_precarias": 1,
                    "escola": {
                        "codigo_integracao": "INT001",
                        "codigo_eol": "123456",
                    },
                    "cargo_codigo": 100,
                },
            ],
        }
        mock_api = MagicMock()
        mock_api.get_vagas_escolas.return_value = payload_valido
        with patch(
            "exporta_arquivo.services.exportacao_vagas_processo.ApiEscolhasService",
            return_value=mock_api,
        ):
            resultado = buscar_vagas_escolas("processo-uuid", 100)
        assert len(resultado) == 1
        assert resultado[0]["codigo_eol"] == "123456"
        assert resultado[0]["vagas_definitivas"] == 2
        assert resultado[0]["vagas_precarias"] == 1
        mock_api.get_vagas_escolas.assert_called_once_with(
            "processo-uuid", 100
        )

    def test_payload_invalido_serializer_levanta_erro(self):
        from rest_framework.exceptions import ValidationError

        payload_invalido = {
            "vagas": []
        }  # validate_vagas exige pelo menos uma vaga
        mock_api = MagicMock()
        mock_api.get_vagas_escolas.return_value = payload_invalido
        with patch(  # noqa: SIM117
            "exporta_arquivo.services.exportacao_vagas_processo.ApiEscolhasService",
            return_value=mock_api,
        ):
            with pytest.raises(ValidationError):
                buscar_vagas_escolas("processo-uuid", 100)

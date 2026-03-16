"""
Testes de funções puras e orquestração do serviço exportacao_candidatos_processo.
Funções puras + validações + exportar_candidatos_processo (com mock de API).
Sem HTTP/DB; mocks no ponto de uso.
"""
import uuid

import pytest

from exporta_arquivo.services.exceptions import (
    ExportacaoBadRequestException,
    ExportacaoNotFoundException,
)
from exporta_arquivo.services.exportacao_candidatos_processo import (
    _campo,
    _cpf_apenas_digitos,
    _data_para_dd_mm_yyyy,
    exportar_candidatos_processo,
    formatar_arquivo_candidatos_processo,
)


class TestDataParaDdMmYyyy:
    """_data_para_dd_mm_yyyy: None, "", ISO com T, YYYY-MM-DD, já DD/MM/YYYY, inválido."""

    def test_none_retorna_vazio(self):
        assert _data_para_dd_mm_yyyy(None) == ""

    def test_string_vazia_retorna_vazio(self):
        assert _data_para_dd_mm_yyyy("") == ""

    def test_iso_com_t_retorna_dd_mm_yyyy(self):
        assert _data_para_dd_mm_yyyy("2024-07-03T00:00:00") == "03/07/2024"

    def test_yyyy_mm_dd_retorna_dd_mm_yyyy(self):
        assert _data_para_dd_mm_yyyy("2024-07-03") == "03/07/2024"

    def test_ja_dd_mm_yyyy_retorna_igual(self):
        assert _data_para_dd_mm_yyyy("03/07/2024") == "03/07/2024"

    def test_invalido_retorna_string_original(self):
        # Sem "-" nem "/" com 8+ chars: retorna s
        assert _data_para_dd_mm_yyyy("invalido") == "invalido"


class TestCpfApenasDigitos:
    """_cpf_apenas_digitos: None, só dígitos, com pontuação, vazio."""

    def test_none_retorna_vazio(self):
        assert _cpf_apenas_digitos(None) == ""

    def test_so_digitos_retorna_igual(self):
        assert _cpf_apenas_digitos("12345678900") == "12345678900"

    def test_com_pontuacao_remove_tudo_que_nao_e_digito(self):
        assert _cpf_apenas_digitos("123.456.789-00") == "12345678900"

    def test_vazio_retorna_vazio(self):
        assert _cpf_apenas_digitos("") == ""


class TestCampo:
    """_campo: None, com pipe, com \\n/\\r."""

    def test_none_retorna_vazio(self):
        assert _campo(None) == ""

    def test_com_pipe_substitui_por_espaco(self):
        assert "|" not in _campo("a|b|c")
        assert " " in _campo("a|b|c")

    def test_com_newline_e_cr_substitui_por_espaco(self):
        assert _campo("linha1\nlinha2") == "linha1 linha2"
        assert _campo("linha1\rlinha2") == "linha1 linha2"


class TestFormatarArquivoCandidatosProcesso:
    """formatar_arquivo_candidatos_processo: lista vazia; 1 linha; várias; codigo/data_criacao; dt_nascimento e cd_cpf."""

    def test_lista_vazia_retorna_string_vazia(self):
        out = formatar_arquivo_candidatos_processo([])
        assert out == ""

    def test_uma_linha_dados_minimos(self):
        linhas = [
            {
                "codigo": 100,
                "data_criacao": "03/07/2024",
                "cd_cpf": "12345678900",
                "nm_candidato_concurso": "Fulano",
                "dt_nascimento": "15/03/1990",
            }
        ]
        out = formatar_arquivo_candidatos_processo(linhas)
        assert out
        assert "100" in out
        assert "03/07/2024" in out
        assert "12345678900" in out
        assert "Fulano" in out
        assert "15/03/1990" in out
        assert out.count("|") >= 20  # várias colunas
        assert out.endswith("\n")

    def test_varias_linhas(self):
        linhas = [
            {"codigo": 1, "data_criacao": "01/01/2024", "cd_cpf": "111", "nm_candidato_concurso": "A", "dt_nascimento": ""},
            {"codigo": 1, "data_criacao": "01/01/2024", "cd_cpf": "222", "nm_candidato_concurso": "B", "dt_nascimento": ""},
        ]
        out = formatar_arquivo_candidatos_processo(linhas)
        linhas_out = out.strip().split("\n")
        assert len(linhas_out) == 2
        assert "111" in linhas_out[0]
        assert "222" in linhas_out[1]

    def test_codigo_none_data_criacao_vazia(self):
        linhas = [
            {"codigo": None, "data_criacao": "", "cd_cpf": "123", "nm_candidato_concurso": "X", "dt_nascimento": ""}
        ]
        out = formatar_arquivo_candidatos_processo(linhas)
        assert out
        assert "123" in out and "X" in out

    def test_dt_nascimento_dd_mm_yyyy_na_saida(self):
        """Valores de dt_nascimento já em DD/MM/YYYY (ex.: vindos do mapeador) aparecem na saída."""
        linhas = [
            {
                "codigo": 1,
                "data_criacao": "01/01/2024",
                "cd_cpf": "12345678900",
                "nm_candidato_concurso": "Y",
                "dt_nascimento": "31/12/1995",
            }
        ]
        out = formatar_arquivo_candidatos_processo(linhas)
        assert "31/12/1995" in out

    def test_cd_cpf_apenas_digitos_na_coluna(self):
        """Coluna cd_cpf na saída reflete o valor do item (já normalizado pelo mapeador)."""
        linhas = [
            {
                "codigo": 1,
                "data_criacao": "01/01/2024",
                "cd_cpf": "12345678900",
                "nm_candidato_concurso": "Z",
                "dt_nascimento": "",
            }
        ]
        out = formatar_arquivo_candidatos_processo(linhas)
        assert "12345678900" in out
        first_line = out.strip().split("\n")[0]
        parts = first_line.split("|")
        assert len(parts) >= 3
        assert parts[2] == "12345678900"

class TestExportarCandidatosProcesso:
    """exportar_candidatos_processo: recebe instance; mock de APIs; retorna conteúdo formatado (str)."""

    @pytest.fixture
    def instance(self):
        """Instance mock com processo_uuid, cargo_uuid, cargo_codigo, concurso_uuid."""
        from unittest.mock import MagicMock
        inst = MagicMock()
        inst.processo_uuid = uuid.uuid4()
        inst.cargo_uuid = uuid.uuid4()
        inst.cargo_codigo = 1
        inst.concurso_uuid = uuid.uuid4()
        return inst

    def test_retorno_vazio_quando_habilitados_vazio(self, instance):
        from unittest.mock import patch

        with patch(
            "exporta_arquivo.services.exportacao_candidatos_processo.ApiConcursosService"
        ) as mock_api_concursos, patch(
            "exporta_arquivo.services.exportacao_candidatos_processo.ApiCandidatosService"
        ) as mock_api_candidatos:
            mock_api_concursos.return_value.get_concurso.return_value = {
                "codigo": 10,
                "criado_em": "2024-01-01T00:00:00",
            }
            mock_api_candidatos.return_value.get_habilitados.return_value = []

            out = exportar_candidatos_processo(instance)

        assert out == ""
        instance.save.assert_called_once()

    def test_retorno_formatado_ordenacao_por_ranking(self, instance):
        from unittest.mock import patch

        habilitados_api = [
            {
                "candidato": {
                    "cpf": "111",
                    "nome": "Candidato A",
                    "data_nascimento": "1990-01-15T00:00:00",
                },
                "codigo_cargo": 100,
                "ranking_escolha": 2,
                "classificacao": 10,
            },
            {
                "candidato": {
                    "cpf": "222",
                    "nome": "Candidato B",
                    "data_nascimento": None,
                },
                "codigo_cargo": 100,
                "ranking_escolha": 1,
                "classificacao": 5,
            },
        ]
        with patch(
            "exporta_arquivo.services.exportacao_candidatos_processo.ApiConcursosService"
        ) as mock_api_concursos, patch(
            "exporta_arquivo.services.exportacao_candidatos_processo.ApiCandidatosService"
        ) as mock_api_candidatos:
            mock_api_concursos.return_value.get_concurso.return_value = {
                "codigo": 200,
                "criado_em": "2024-06-01T00:00:00",
            }
            mock_api_candidatos.return_value.get_habilitados.return_value = habilitados_api

            out = exportar_candidatos_processo(instance)

        assert out
        assert out.endswith("\n")
        linhas = out.strip().split("\n")
        assert len(linhas) == 2
        # Ordenação por ranking_escolha: 1 antes de 2 → Candidato B primeiro
        assert "Candidato B" in linhas[0]
        assert "222" in linhas[0]
        assert "Candidato A" in linhas[1]
        assert "111" in linhas[1]
        assert "15/01/1990" in out  # dt_nascimento em DD/MM/YYYY (1990-01-15)

    def test_atualiza_instance_com_dados_concurso_e_retorna_string(self, instance):
        from unittest.mock import patch

        with patch(
            "exporta_arquivo.services.exportacao_candidatos_processo.ApiConcursosService"
        ) as mock_api_concursos, patch(
            "exporta_arquivo.services.exportacao_candidatos_processo.ApiCandidatosService"
        ) as mock_api_candidatos:
            mock_api_concursos.return_value.get_concurso.return_value = {
                "codigo": 99,
                "criado_em": "2024-06-01T00:00:00",
            }
            mock_api_candidatos.return_value.get_habilitados.return_value = []

            out = exportar_candidatos_processo(instance)

        assert out == ""
        assert instance.concurso_codigo == 99
        assert instance.concurso_data_criacao == "2024-06-01T00:00:00"
        instance.save.assert_called_once_with(update_fields=["concurso_codigo", "concurso_data_criacao"])

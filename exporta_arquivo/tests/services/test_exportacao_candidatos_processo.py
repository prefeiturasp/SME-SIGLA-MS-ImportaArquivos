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
    _validar_cargo_codigo,
    _validar_concurso_codigo,
    _validar_concurso_uuid,
    _validar_uuids_processo_cargo,
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
        out = formatar_arquivo_candidatos_processo(
            dados_concurso={"codigo": 1, "data_criacao": "01/01/2024"},
            linhas_candidatos=[],
        )
        assert out == ""

    def test_uma_linha_dados_minimos(self):
        dados = {"codigo": 100, "data_criacao": "03/07/2024", "cargo_codigo": 1, "cargo_nome": "Cargo"}
        linhas = [
            {
                "cd_cpf": "12345678900",
                "nm_candidato_concurso": "Fulano",
                "dt_nascimento": "15/03/1990",
            }
        ]
        out = formatar_arquivo_candidatos_processo(dados, linhas)
        assert out
        assert "100" in out
        assert "03/07/2024" in out
        assert "12345678900" in out
        assert "Fulano" in out
        assert "15/03/1990" in out
        assert out.count("|") >= 20  # várias colunas
        assert out.endswith("\n")

    def test_varias_linhas(self):
        dados = {"codigo": 1, "data_criacao": "01/01/2024"}
        linhas = [
            {"cd_cpf": "111", "nm_candidato_concurso": "A", "dt_nascimento": ""},
            {"cd_cpf": "222", "nm_candidato_concurso": "B", "dt_nascimento": ""},
        ]
        out = formatar_arquivo_candidatos_processo(dados, linhas)
        linhas_out = out.strip().split("\n")
        assert len(linhas_out) == 2
        assert "111" in linhas_out[0]
        assert "222" in linhas_out[1]

    def test_codigo_none_data_criacao_vazia(self):
        dados = {"codigo": None, "data_criacao": ""}
        linhas = [{"cd_cpf": "123", "nm_candidato_concurso": "X", "dt_nascimento": ""}]
        out = formatar_arquivo_candidatos_processo(dados, linhas)
        assert out
        assert "123" in out and "X" in out

    def test_dt_nascimento_iso_formatado_dd_mm_yyyy(self):
        dados = {"codigo": 1, "data_criacao": "01/01/2024"}
        linhas = [
            {
                "cd_cpf": "12345678900",
                "nm_candidato_concurso": "Y",
                "dt_nascimento": "1995-12-31T00:00:00",
            }
        ]
        out = formatar_arquivo_candidatos_processo(dados, linhas)
        assert "31/12/1995" in out

    def test_cd_cpf_com_pontuacao_sai_so_digitos(self):
        dados = {"codigo": 1, "data_criacao": "01/01/2024"}
        linhas = [
            {
                "cd_cpf": "123.456.789-00",
                "nm_candidato_concurso": "Z",
                "dt_nascimento": "",
            }
        ]
        out = formatar_arquivo_candidatos_processo(dados, linhas)
        assert "12345678900" in out
        assert "123.456.789-00" not in out or "123.456.789-00" in out  # coluna cd_cpf deve ter só dígitos
        # A coluna cd_cpf é formatada por _cpf_apenas_digitos, então deve aparecer só dígitos
        first_line = out.strip().split("\n")[0]
        # Terceira coluna é cd_cpf (codigo, data_criacao, cd_cpf, ...)
        parts = first_line.split("|")
        assert len(parts) >= 3
        assert parts[2] == "12345678900"


# --- Validações e orquestração (com mocks) ---


class TestValidarUuidsProcessoCargo:
    """_validar_uuids_processo_cargo: UUID válido; processo_uuid inválido; cargo_uuid inválido."""

    def test_uuid_valido_nao_levanta(self):
        p = str(uuid.uuid4())
        c = str(uuid.uuid4())
        _validar_uuids_processo_cargo(p, c)  # no raise

    def test_processo_uuid_invalido_levanta_exportacao_not_found(self):
        with pytest.raises(ExportacaoNotFoundException) as exc_info:
            _validar_uuids_processo_cargo("nao-e-uuid", str(uuid.uuid4()))
        assert "processo_uuid" in str(exc_info.value)
        assert "inválido" in str(exc_info.value).lower()

    def test_cargo_uuid_invalido_levanta_exportacao_not_found(self):
        with pytest.raises(ExportacaoNotFoundException) as exc_info:
            _validar_uuids_processo_cargo(str(uuid.uuid4()), "x")
        assert "cargo_uuid" in str(exc_info.value)
        assert "inválido" in str(exc_info.value).lower()


class TestValidarCargoCodigo:
    """_validar_cargo_codigo: None, não numérico, válido."""

    def test_none_levanta_bad_request(self):
        with pytest.raises(ExportacaoBadRequestException) as exc_info:
            _validar_cargo_codigo(None)
        assert "cargo_codigo" in str(exc_info.value).lower()
        assert "obrigatório" in str(exc_info.value).lower() or "ausente" in str(exc_info.value).lower()

    def test_nao_numerico_levanta_bad_request(self):
        with pytest.raises(ExportacaoBadRequestException) as exc_info:
            _validar_cargo_codigo("abc")
        assert "cargo_codigo" in str(exc_info.value).lower()
        assert "numérico" in str(exc_info.value).lower()

    def test_valido_retorna_int(self):
        assert _validar_cargo_codigo(100) == 100
        assert _validar_cargo_codigo("100") == 100


class TestValidarConcursoUuid:
    """_validar_concurso_uuid: inválido vs válido/None."""

    def test_none_ou_vazio_nao_levanta(self):
        _validar_concurso_uuid(None)
        _validar_concurso_uuid("")

    def test_uuid_valido_nao_levanta(self):
        _validar_concurso_uuid(str(uuid.uuid4()))

    def test_uuid_invalido_levanta_not_found(self):
        with pytest.raises(ExportacaoNotFoundException) as exc_info:
            _validar_concurso_uuid("invalido")
        assert "concurso_uuid" in str(exc_info.value).lower()


class TestValidarConcursoCodigo:
    """_validar_concurso_codigo: None, não numérico, válido."""

    def test_none_levanta_bad_request(self):
        with pytest.raises(ExportacaoBadRequestException) as exc_info:
            _validar_concurso_codigo(None)
        assert "concurso_codigo" in str(exc_info.value).lower()

    def test_nao_numerico_levanta_bad_request(self):
        with pytest.raises(ExportacaoBadRequestException):
            _validar_concurso_codigo("xyz")

    def test_valido_retorna_int(self):
        assert _validar_concurso_codigo(5) == 5
        assert _validar_concurso_codigo("10") == 10


class TestExportarCandidatosProcesso:
    """exportar_candidatos_processo: mock de _buscar_habilitados; formato e ordenação."""

    @pytest.fixture
    def processo_uuid(self):
        return str(uuid.uuid4())

    @pytest.fixture
    def cargo_uuid(self):
        return str(uuid.uuid4())

    def test_retorno_vazio_quando_buscar_habilitados_vazio(self, processo_uuid, cargo_uuid):
        from unittest.mock import patch

        with patch(
            "exporta_arquivo.services.exportacao_candidatos_processo._buscar_habilitados",
            return_value=[],
        ):
            dados, lista = exportar_candidatos_processo(
                processo_uuid, cargo_uuid, cargo_codigo=1,
            )
        assert dados["cargo_codigo"] == 1
        assert dados["codigo"] is None
        assert dados["data_criacao"] == ""
        assert "processo_uuid" in dados
        assert lista == []

    def test_dados_concurso_e_lista_formato_esperado_ordenacao_ranking(self, processo_uuid, cargo_uuid):
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
            "exporta_arquivo.services.exportacao_candidatos_processo._buscar_habilitados",
            return_value=habilitados_api,
        ):
            dados, lista = exportar_candidatos_processo(
                processo_uuid, cargo_uuid, cargo_codigo=200,
            )
        assert dados["cargo_codigo"] == 200
        assert len(lista) == 2
        # Ordenação por ranking_escolha: 1 antes de 2
        assert lista[0]["nm_candidato_concurso"] == "Candidato B"
        assert lista[0]["nr_classificação"] == 1
        assert lista[1]["nm_candidato_concurso"] == "Candidato A"
        assert lista[1]["nr_classificação"] == 2
        assert lista[0]["cd_cpf"] == "222"
        assert lista[1]["cd_cpf"] == "111"
        # Mapeador deixa dt_nascimento em YYYY-MM-DD; DD/MM/YYYY é aplicado no formatar_arquivo
        assert lista[1]["dt_nascimento"] == "1990-01-15"

    def test_concurso_uuid_e_codigo_data_preenchem_dados_concurso(self, processo_uuid, cargo_uuid):
        from unittest.mock import patch

        with patch(
            "exporta_arquivo.services.exportacao_candidatos_processo._buscar_habilitados",
            return_value=[],
        ):
            dados, _ = exportar_candidatos_processo(
                processo_uuid,
                cargo_uuid,
                concurso_uuid=str(uuid.uuid4()),
                cargo_codigo=1,
                concurso_codigo=99,
                concurso_data_criacao="01/06/2024",
            )
        assert dados["codigo"] == 99
        assert dados["data_criacao"] == "01/06/2024"

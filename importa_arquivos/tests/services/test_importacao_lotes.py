"""
Testes do serviço importacao_lotes.py:
- _validar_linha_lote: linha válida, lote divergente, erro pydantic
- validar_txt_lotes: arquivo vazio, colunas faltando, linha inválida, sucesso,
linhas vazias ignoradas
Sem DB (importacao_obj=None).
"""

from unittest.mock import MagicMock

import pytest

from importa_arquivos.services.exceptions import (
    ArquivoLotesVazioException,
    ColunaCSVInvalidaException,
    ErrosValidacaoLotesException,
    LeituraCSVException,
)
from importa_arquivos.services.importacao_lotes import (
    _validar_linha_lote,
    validar_txt_lotes,
)

# ─── helpers ────────────────────────────────────────────────────────────────

HEADER = "LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC\n"


def _linha(
    lote=1,
    empresa="EMP01",
    vaga="VAGA01",
    identificacao=100,
    chave="CH01",
    numfunc=999,
    numvinc=1,
):
    return f"{lote};{empresa};{vaga};{identificacao};{chave};{numfunc};{numvinc}\n"  # noqa: E501


def _arquivo_txt(conteudo: str) -> MagicMock:
    """Cria um arquivo fake com read()/seek() para testes."""
    encoded = conteudo.encode("utf-8")
    arquivo = MagicMock()
    arquivo.read.return_value = encoded
    arquivo.seek.return_value = None
    return arquivo


# ─── _validar_linha_lote ────────────────────────────────────────────────────


class TestValidarLinhaLote:
    """Testa a validação individual de linha."""

    def _row(
        self,
        lote="1",
        empresa="EMP",
        vaga="VAG",
        identificacao="100",
        chave="CH",
        numfunc="999",
        numvinc="1",
    ):
        return {
            "LOTE": lote,
            "EMPRESA": empresa,
            "VAGA": vaga,
            "IDENTIFICACAO": identificacao,
            "CHAVE_INSCRITO": chave,
            "NUMFUNC": numfunc,
            "NUMVINC": numvinc,
        }

    def test_linha_valida_retorna_objeto_e_sem_erro(self):
        obj, erro, lote_ref = _validar_linha_lote(self._row(), 1, None)
        assert obj is not None
        assert erro == ""
        assert lote_ref == 1

    def test_lote_referencia_definido_na_primeira_linha(self):
        _, _, lote_ref = _validar_linha_lote(self._row(lote="5"), 1, None)
        assert lote_ref == 5

    def test_lote_igual_ao_referencia_passa(self):
        obj, erro, lote_ref = _validar_linha_lote(self._row(lote="3"), 2, 3)
        assert obj is not None
        assert erro == ""

    def test_lote_divergente_retorna_erro(self):
        obj, erro, lote_ref = _validar_linha_lote(self._row(lote="9"), 2, 1)
        assert obj is None
        assert "diverge" in erro.lower() or "lote" in erro.lower()
        assert lote_ref == 1  # não muda

    def test_empresa_vazia_retorna_erro_pydantic(self):
        row = self._row(empresa="")
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is None
        assert "empresa" in erro.lower() or "linha" in erro.lower()

    def test_vaga_vazia_retorna_erro_pydantic(self):
        row = self._row(vaga="   ")
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is None
        assert "vaga" in erro.lower() or "linha" in erro.lower()

    def test_lote_nao_numerico_retorna_erro(self):
        row = self._row(lote="abc")
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is None
        assert erro != ""

    def test_numvinc_opcional_pode_ser_none(self):
        row = self._row(numvinc="")
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is not None
        assert obj.numvinc is None

    def test_numero_linha_aparece_na_mensagem_de_erro(self):
        row = self._row(empresa="")
        _, erro, _ = _validar_linha_lote(row, 7, None)
        assert "7" in erro


# ─── validar_txt_lotes ──────────────────────────────────────────────────────


class TestValidarTxtLotes:
    """Testa a função principal de leitura e validação do arquivo TXT."""

    def test_arquivo_valido_retorna_lista_de_dicts(self):
        conteudo = HEADER + _linha()
        resultado = validar_txt_lotes(
            _arquivo_txt(conteudo), importacao_obj=None
        )
        assert isinstance(resultado, list)
        assert len(resultado) == 1
        assert resultado[0]["lote"] == 1
        assert resultado[0]["empresa"] == "EMP01"

    def test_multiplas_linhas_validas(self):
        conteudo = HEADER + _linha(identificacao=1) + _linha(identificacao=2)
        resultado = validar_txt_lotes(
            _arquivo_txt(conteudo), importacao_obj=None
        )
        assert len(resultado) == 2

    def test_arquivo_vazio_levanta_excecao(self):
        with pytest.raises(ArquivoLotesVazioException):
            validar_txt_lotes(_arquivo_txt(""), importacao_obj=None)

    def test_arquivo_so_espacos_levanta_excecao(self):
        with pytest.raises(ArquivoLotesVazioException):
            validar_txt_lotes(_arquivo_txt("   \n\n"), importacao_obj=None)

    def test_somente_cabecalho_sem_dados_levanta_excecao_vazio(self):
        with pytest.raises(ArquivoLotesVazioException):
            validar_txt_lotes(_arquivo_txt(HEADER), importacao_obj=None)

    def test_coluna_faltando_levanta_coluna_invalida(self):
        # Sem NUMVINC
        header_incompleto = (
            "LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC\n"
        )
        conteudo = header_incompleto + "1;EMP;VAG;100;CH;999\n"
        with pytest.raises(ColunaCSVInvalidaException) as exc_info:
            validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert "NUMVINC" in exc_info.value.detalhes

    def test_linha_invalida_levanta_erros_validacao(self):
        # Uma linha válida + uma linha com lote divergente → ErrosValidacaoLotesException  # noqa: E501
        conteudo = (
            HEADER
            + _linha(lote=1, identificacao=10)
            + _linha(lote=2, identificacao=11)
        )
        with pytest.raises(ErrosValidacaoLotesException) as exc_info:
            validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert "diverge" in exc_info.value.detalhes.lower()

    def test_leitura_falha_levanta_leitura_csv(self):
        arquivo = MagicMock()
        arquivo.read.side_effect = OSError("disk error")
        with pytest.raises(LeituraCSVException):
            validar_txt_lotes(arquivo, importacao_obj=None)

    def test_linha_completamente_vazia_ignorada(self):
        conteudo = (
            HEADER
            + _linha(identificacao=10)
            + ";;;;\n"
            + _linha(identificacao=11)
        )
        resultado = validar_txt_lotes(
            _arquivo_txt(conteudo), importacao_obj=None
        )
        assert len(resultado) == 2

    def test_campos_model_dump_retornados(self):
        conteudo = HEADER + _linha(
            lote=7, empresa="EMPX", numfunc=42, numvinc=3
        )
        resultado = validar_txt_lotes(
            _arquivo_txt(conteudo), importacao_obj=None
        )
        assert resultado[0]["lote"] == 7
        assert resultado[0]["empresa"] == "EMPX"
        assert resultado[0]["numfunc"] == 42
        assert resultado[0]["numvinc"] == 3

    def test_arquivo_com_bom_utf8_sig_decodificado(self):
        """Arquivo com BOM (utf-8-sig) deve ser lido corretamente."""
        conteudo = HEADER + _linha()
        arquivo = MagicMock()
        # utf-8-sig insere o BOM automaticamente; o serviço usa decode('utf-8-sig') para removê-lo  # noqa: E501
        arquivo.read.return_value = conteudo.encode("utf-8-sig")
        arquivo.seek.return_value = None
        resultado = validar_txt_lotes(arquivo, importacao_obj=None)
        assert len(resultado) == 1

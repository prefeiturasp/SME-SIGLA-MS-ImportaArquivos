"""Testes do serviço importacao_lotes.py:.

- _validar_linha_lote: linha válida, lote divergente, erro pydantic
- validar_txt_lotes: arquivo vazio, colunas faltando, linha inválida, sucesso,
linhas vazias ignoradas
Sem DB (importacao_obj=None).
"""
from __future__ import annotations
from typing import Any
from unittest.mock import MagicMock
import pytest
from importa_arquivos.services.exceptions import ArquivoLotesVazioException, ColunaCSVInvalidaException, ErrosValidacaoLotesException, LeituraCSVException
from importa_arquivos.services.importacao_lotes import _validar_linha_lote, validar_txt_lotes
HEADER = 'LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC\n'

def _linha(lote: Any=1, empresa: Any='EMP01', vaga: Any='VAGA01', identificacao: Any=100, chave: Any='CH01', numfunc: Any=999, numvinc: Any=1) -> Any:
    """Executa  linha.
    
    Args:
        lote: Parâmetro lote da operação.
        empresa: Parâmetro empresa da operação.
        vaga: Parâmetro vaga da operação.
        identificacao: Parâmetro identificacao da operação.
        chave: Parâmetro chave da operação.
        numfunc: Parâmetro numfunc da operação.
        numvinc: Parâmetro numvinc da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return f'{lote};{empresa};{vaga};{identificacao};{chave};{numfunc};{numvinc}\n'

def _arquivo_txt(conteudo: str) -> MagicMock:
    """Cria um arquivo fake com read()/seek() para testes.
    
    Args:
        conteudo: Parâmetro conteudo da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    encoded = conteudo.encode('utf-8')
    arquivo = MagicMock()
    arquivo.read.return_value = encoded
    arquivo.seek.return_value = None
    return arquivo

class TestValidarLinhaLote:
    """Testa a validação individual de linha."""

    def _row(self, lote: Any='1', empresa: Any='EMP', vaga: Any='VAG', identificacao: Any='100', chave: Any='CH', numfunc: Any='999', numvinc: Any='1') -> Any:
        """Executa  row.
        
        Args:
            self: Instância do objeto.
            lote: Parâmetro lote da operação.
            empresa: Parâmetro empresa da operação.
            vaga: Parâmetro vaga da operação.
            identificacao: Parâmetro identificacao da operação.
            chave: Parâmetro chave da operação.
            numfunc: Parâmetro numfunc da operação.
            numvinc: Parâmetro numvinc da operação.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return {'LOTE': lote, 'EMPRESA': empresa, 'VAGA': vaga, 'IDENTIFICACAO': identificacao, 'CHAVE_INSCRITO': chave, 'NUMFUNC': numfunc, 'NUMVINC': numvinc}

    def test_linha_valida_retorna_objeto_e_sem_erro(self) -> None:
        """Verifica linha valida retorna objeto e sem erro.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        obj, erro, lote_ref = _validar_linha_lote(self._row(), 1, None)
        assert obj is not None
        assert erro == ''
        assert lote_ref == 1

    def test_lote_referencia_definido_na_primeira_linha(self) -> None:
        """Verifica lote referencia definido na primeira linha.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        _, _, lote_ref = _validar_linha_lote(self._row(lote='5'), 1, None)
        assert lote_ref == 5

    def test_lote_igual_ao_referencia_passa(self) -> None:
        """Verifica lote igual ao referencia passa.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        obj, erro, lote_ref = _validar_linha_lote(self._row(lote='3'), 2, 3)
        assert obj is not None
        assert erro == ''

    def test_lote_divergente_retorna_erro(self) -> None:
        """Verifica lote divergente retorna erro.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        obj, erro, lote_ref = _validar_linha_lote(self._row(lote='9'), 2, 1)
        assert obj is None
        assert 'diverge' in erro.lower() or 'lote' in erro.lower()
        assert lote_ref == 1

    def test_empresa_vazia_retorna_erro_pydantic(self) -> None:
        """Verifica empresa vazia retorna erro pydantic.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        row = self._row(empresa='')
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is None
        assert 'empresa' in erro.lower() or 'linha' in erro.lower()

    def test_vaga_vazia_retorna_erro_pydantic(self) -> None:
        """Verifica vaga vazia retorna erro pydantic.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        row = self._row(vaga='   ')
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is None
        assert 'vaga' in erro.lower() or 'linha' in erro.lower()

    def test_lote_nao_numerico_retorna_erro(self) -> None:
        """Verifica lote nao numerico retorna erro.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        row = self._row(lote='abc')
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is None
        assert erro != ''

    def test_numvinc_opcional_pode_ser_none(self) -> None:
        """Verifica numvinc opcional pode ser none.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        row = self._row(numvinc='')
        obj, erro, _ = _validar_linha_lote(row, 1, None)
        assert obj is not None
        assert obj.numvinc is None

    def test_numero_linha_aparece_na_mensagem_de_erro(self) -> None:
        """Verifica numero linha aparece na mensagem de erro.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        row = self._row(empresa='')
        _, erro, _ = _validar_linha_lote(row, 7, None)
        assert '7' in erro

class TestValidarTxtLotes:
    """Testa a função principal de leitura e validação do arquivo TXT."""

    def test_arquivo_valido_retorna_lista_de_dicts(self) -> None:
        """Verifica arquivo valido retorna lista de dicts.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        conteudo = HEADER + _linha()
        resultado = validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert isinstance(resultado, list)
        assert len(resultado) == 1
        assert resultado[0]['lote'] == 1
        assert resultado[0]['empresa'] == 'EMP01'

    def test_multiplas_linhas_validas(self) -> None:
        """Verifica multiplas linhas validas.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        conteudo = HEADER + _linha(identificacao=1) + _linha(identificacao=2)
        resultado = validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert len(resultado) == 2

    def test_arquivo_vazio_levanta_excecao(self) -> None:
        """Verifica arquivo vazio levanta excecao.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        with pytest.raises(ArquivoLotesVazioException):
            validar_txt_lotes(_arquivo_txt(''), importacao_obj=None)

    def test_arquivo_so_espacos_levanta_excecao(self) -> None:
        """Verifica arquivo so espacos levanta excecao.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        with pytest.raises(ArquivoLotesVazioException):
            validar_txt_lotes(_arquivo_txt('   \n\n'), importacao_obj=None)

    def test_somente_cabecalho_sem_dados_levanta_excecao_vazio(self) -> None:
        """Verifica somente cabecalho sem dados levanta excecao vazio.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        with pytest.raises(ArquivoLotesVazioException):
            validar_txt_lotes(_arquivo_txt(HEADER), importacao_obj=None)

    def test_coluna_faltando_levanta_coluna_invalida(self) -> None:
        """Verifica coluna faltando levanta coluna invalida.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        header_incompleto = 'LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC\n'
        conteudo = header_incompleto + '1;EMP;VAG;100;CH;999\n'
        with pytest.raises(ColunaCSVInvalidaException) as exc_info:
            validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert 'NUMVINC' in exc_info.value.detalhes

    def test_linha_invalida_levanta_erros_validacao(self) -> None:
        """Verifica linha invalida levanta erros validacao.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        conteudo = HEADER + _linha(lote=1, identificacao=10) + _linha(lote=2, identificacao=11)
        with pytest.raises(ErrosValidacaoLotesException) as exc_info:
            validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert 'diverge' in exc_info.value.detalhes.lower()

    def test_leitura_falha_levanta_leitura_csv(self) -> None:
        """Verifica leitura falha levanta leitura csv.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        arquivo = MagicMock()
        arquivo.read.side_effect = OSError('disk error')
        with pytest.raises(LeituraCSVException):
            validar_txt_lotes(arquivo, importacao_obj=None)

    def test_linha_completamente_vazia_ignorada(self) -> None:
        """Verifica linha completamente vazia ignorada.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        conteudo = HEADER + _linha(identificacao=10) + ';;;;\n' + _linha(identificacao=11)
        resultado = validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert len(resultado) == 2

    def test_campos_model_dump_retornados(self) -> None:
        """Verifica campos model dump retornados.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        conteudo = HEADER + _linha(lote=7, empresa='EMPX', numfunc=42, numvinc=3)
        resultado = validar_txt_lotes(_arquivo_txt(conteudo), importacao_obj=None)
        assert resultado[0]['lote'] == 7
        assert resultado[0]['empresa'] == 'EMPX'
        assert resultado[0]['numfunc'] == 42
        assert resultado[0]['numvinc'] == 3

    def test_arquivo_com_bom_utf8_sig_decodificado(self) -> None:
        """Arquivo com BOM (utf-8-sig) deve ser lido corretamente.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        conteudo = HEADER + _linha()
        arquivo = MagicMock()
        arquivo.read.return_value = conteudo.encode('utf-8-sig')
        arquivo.seek.return_value = None
        resultado = validar_txt_lotes(arquivo, importacao_obj=None)
        assert len(resultado) == 1

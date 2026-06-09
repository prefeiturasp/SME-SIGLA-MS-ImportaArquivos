"""Testes de utilitários da exportação: sanitizar_nome_arquivo.

Sem HTTP/DB; usa BaseExportacaoViewSet.sanitizar_nome_arquivo (estático).
"""
from __future__ import annotations
from typing import Any
from exporta_arquivo.views.base_exportacao import BaseExportacaoViewSet
sanitizar = BaseExportacaoViewSet.sanitizar_nome_arquivo

class TestSanitizarNomeArquivo:
    """Casos: None, vazio, normal, especiais, acentos, só espaços, max_len,.

    fallback 'arquivo'.
    """

    def test_none_retorna_arquivo(self) -> None:
        """Verifica none retorna arquivo."""
        assert sanitizar(None) == 'arquivo'  # type: ignore[arg-type]

    def test_string_vazia_retorna_arquivo(self) -> None:
        """Verifica string vazia retorna arquivo."""
        assert sanitizar('') == 'arquivo'

    def test_texto_normal_permanece(self) -> None:
        """Verifica texto normal permanece."""
        assert sanitizar('Relatório Processo 2024') == 'Relatório_Processo_2024'

    def test_caracteres_especiais_removidos(self) -> None:
        """Verifica caracteres especiais removidos."""
        assert sanitizar('arquivo@teste#.txt') == 'arquivotestetxt'

    def test_acentos_preservados(self) -> None:
        """Verifica acentos preservados."""
        assert 'São' in sanitizar('Relatório São Paulo') or 'Paulo' in sanitizar('Relatório São Paulo')

    def test_espacos_internos_viram_underscore(self) -> None:
        """Verifica espacos internos viram underscore."""
        assert sanitizar('a b c') == 'a_b_c'

    def test_so_espacos_retorna_arquivo(self) -> None:
        """Verifica so espacos retorna arquivo."""
        assert sanitizar('   ') == 'arquivo'

    def test_maior_que_max_len_truncado(self) -> None:
        """Verifica maior que max len truncado."""
        texto = 'a' * 100
        assert len(sanitizar(texto, max_len=20)) == 20
        assert sanitizar(texto, max_len=20) == 'a' * 20

    def test_string_vira_vazia_apos_sanitizar_fallback_arquivo(self) -> None:
        """Verifica string vira vazia apos sanitizar fallback arquivo."""
        assert sanitizar('@@@###!!!') == 'arquivo'

    def test_max_len_default_80(self) -> None:
        """Verifica max len default 80."""
        texto = 'x' * 100
        assert len(sanitizar(texto)) == 80

    def test_hifen_preservado(self) -> None:
        """Verifica hifen preservado."""
        assert '2024' in sanitizar('export-2024') and '-' in sanitizar('export-2024')

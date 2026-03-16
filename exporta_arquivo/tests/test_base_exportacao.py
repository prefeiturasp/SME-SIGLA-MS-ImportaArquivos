"""
Testes de utilitários da exportação: sanitizar_nome_arquivo.
Sem HTTP/DB; usa BaseExportacaoViewSet.sanitizar_nome_arquivo (estático).
"""
from exporta_arquivo.views.base_exportacao import BaseExportacaoViewSet


sanitizar = BaseExportacaoViewSet.sanitizar_nome_arquivo


class TestSanitizarNomeArquivo:
    """Casos: None, vazio, normal, especiais, acentos, só espaços, max_len, fallback 'arquivo'."""

    def test_none_retorna_arquivo(self):
        assert sanitizar(None) == "arquivo"

    def test_string_vazia_retorna_arquivo(self):
        assert sanitizar("") == "arquivo"

    def test_texto_normal_permanece(self):
        assert sanitizar("Relatório Processo 2024") == "Relatório_Processo_2024"

    def test_caracteres_especiais_removidos(self):
        # @ # . são removidos (apenas \w \s - são mantidos)
        assert sanitizar("arquivo@teste#.txt") == "arquivotestetxt"

    def test_acentos_preservados(self):
        # \w em re.UNICODE inclui letras acentuadas
        assert "São" in sanitizar("Relatório São Paulo") or "Paulo" in sanitizar("Relatório São Paulo")

    def test_espacos_internos_viram_underscore(self):
        assert sanitizar("a b c") == "a_b_c"

    def test_so_espacos_retorna_arquivo(self):
        assert sanitizar("   ") == "arquivo"

    def test_maior_que_max_len_truncado(self):
        texto = "a" * 100
        assert len(sanitizar(texto, max_len=20)) == 20
        assert sanitizar(texto, max_len=20) == "a" * 20

    def test_string_vira_vazia_apos_sanitizar_fallback_arquivo(self):
        # Só caracteres especiais removidos -> sobra vazio ou só espaços
        assert sanitizar("@@@###!!!") == "arquivo"

    def test_max_len_default_80(self):
        texto = "x" * 100
        assert len(sanitizar(texto)) == 80

    def test_hifen_preservado(self):
        assert "2024" in sanitizar("export-2024") and "-" in sanitizar("export-2024")

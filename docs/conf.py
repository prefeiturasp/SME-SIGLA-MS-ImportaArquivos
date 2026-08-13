"""Configuração do Sphinx do Módulo de Importação/Exportação de Arquivos."""

project = "Módulo de Importação e Exportação de Arquivos"
author = "SME - SIGLA"
copyright = "2026, SME - SIGLA"

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "pt_BR"

html_theme = "alabaster"

html_theme_options = {
    "description": (
        "Documentação do módulo de importação e exportação"
        " de arquivos da SIGLA."
    ),
    "github_button": False,
}

"""Constantes de choices dos models de importação."""

CHOICES_TIPO_IMPORTACAO_ARQUIVO = [
    ("HABILITADOS", "Habilitados"),
    ("VAGAS", "Vagas"),
    ("LOTES", "Lotes"),
]


CHOICES_STATUS_IMPORTACAO_ARQUIVO = [
    ("PENDENTE", "Pendente"),
    ("PROCESSANDO", "Processando"),
    ("CONCLUIDO", "Concluído"),
    ("ERRO", "Erro"),
]


MODO_IMPORTACAO_MANUAL = "MANUAL"
MODO_IMPORTACAO_AUTOMATICA = "AUTOMATICA"
CHOICES_MODO_IMPORTACAO_ESCOLHAS = [
    (MODO_IMPORTACAO_MANUAL, "Manual"),
    (MODO_IMPORTACAO_AUTOMATICA, "Automática"),
]

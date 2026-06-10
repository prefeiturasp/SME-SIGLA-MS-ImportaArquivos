"""Comando para criar o cabeçalho padrão de exportação de lote.

Cria um registro de CabecalhoExportacaoLote com os valores padrão do formato
ERGON/SIGPEC. Se já existir um registro ativo, não cria duplicata (use --force
para sobrescrever).

Uso:
    python manage.py criar_cabecalho_exportacao_lote
    python manage.py criar_cabecalho_exportacao_lote --force
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from exporta_arquivo.models import CabecalhoExportacaoLote

TABELA_PADRAO = "[c_ERGON][PMSP_ESCOLHA_VAGA_SME][1.0]"
CHAVE_PADRAO = "[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER]"
COLUNAS_PADRAO = (
    "[ID_LOTE][NUMBER][EMP_CODIGO][NUMBER][CHAVE_INSCRITO][NUMBER]"
    "[DATA_ESCOLHA][DATE][ESCOLHEU_VAGA][VARCHAR2][SETOR][VARCHAR2]"
)


class Command(BaseCommand):
    """Cria o cabeçalho padrão de exportação de lotes ERGON/SIGPEC."""

    help = (
        "Cria o cabeçalho padrão para exportação de lotes "
        "(formato ERGON/SIGPEC)"
    )

    def add_arguments(self, parser: Any) -> None:
        """Registra os argumentos da linha de comando."""
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Desativa registros existentes e cria um novo "
                "cabeçalho padrão"
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Cria ou recria o cabeçalho padrão de exportação."""
        force = options["force"]
        existente = CabecalhoExportacaoLote.objects.filter(ativo=True).first()
        if existente and (not force):
            self.stdout.write(
                self.style.WARNING(
                    f"Já existe um cabeçalho ativo (UUID={existente.uuid}). "
                    "Use --force para criar um novo desativando o atual."
                )
            )
            return
        if force and existente:
            CabecalhoExportacaoLote.objects.filter(ativo=True).update(
                ativo=False
            )
            self.stdout.write(
                self.style.WARNING(
                    f"Cabeçalho anterior (UUID={existente.uuid}) desativado."
                )
            )
        cabecalho = CabecalhoExportacaoLote.objects.create(
            tabela=TABELA_PADRAO,
            chave=CHAVE_PADRAO,
            tag_inicio="",
            tag_fim="",
            separador=";",
            formato_data="DD/MM/YYYY",
            colunas=COLUNAS_PADRAO,
            ativo=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Cabeçalho criado com sucesso! UUID={cabecalho.uuid}"
            )
        )
        self.stdout.write("")
        self.stdout.write("Conteúdo gerado:")
        self.stdout.write(cabecalho.render())

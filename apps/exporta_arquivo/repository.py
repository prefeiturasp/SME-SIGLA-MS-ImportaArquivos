"""Repositórios de acesso a dados do app exporta_arquivo."""

from __future__ import annotations

from typing import Any

from exporta_arquivo.models import (
    CabecalhoExportacaoLote,
    ExportacaoCandidatosProcesso,
    ExportacaoVagasProcesso,
    ExportacaoVagasSigpec,
)
from exporta_arquivo.models.exportacao_lote import ExportacaoLote


class CabecalhoExportacaoLoteRepository:
    """Consultas e persistência do cabeçalho configurável de exportação."""

    @staticmethod
    def obter_ativo() -> CabecalhoExportacaoLote | None:
        """Retorna o cabeçalho ativo ou None."""
        return CabecalhoExportacaoLote.objects.filter(ativo=True).first()

    @staticmethod
    def desativar_todos_ativos() -> int:
        """Desativa todos os cabeçalhos ativos.

        Returns:
            Quantidade de registros afetados.
        """
        return CabecalhoExportacaoLote.objects.filter(ativo=True).update(
            ativo=False
        )

    @staticmethod
    def criar(**dados: Any) -> CabecalhoExportacaoLote:
        """Cria um cabeçalho de exportação de lote."""
        return CabecalhoExportacaoLote.objects.create(**dados)


class ExportacaoLoteRepository:
    """Persistência de registros de exportação de lote."""

    @classmethod
    def atualizar(cls, instancia: ExportacaoLote, **campos: Any) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))


class ExportacaoCandidatosProcessoRepository:
    """Persistência de registros de exportação de candidatos por processo."""

    @classmethod
    def atualizar(
        cls, instancia: ExportacaoCandidatosProcesso, **campos: Any
    ) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))


class ExportacaoVagasProcessoRepository:
    """Persistência de registros de exportação de vagas por processo."""

    @classmethod
    def atualizar(
        cls, instancia: ExportacaoVagasProcesso, **campos: Any
    ) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))


class ExportacaoVagasSigpecRepository:
    """Persistência de registros de exportação de vagas SIGPEC."""

    @classmethod
    def atualizar(
        cls, instancia: ExportacaoVagasSigpec, **campos: Any
    ) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))

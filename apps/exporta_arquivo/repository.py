"""Repositórios de acesso a dados do app exporta_arquivo."""

from __future__ import annotations

from typing import Any

from exporta_arquivo.models import (
    CabecalhoExportacaoLote,
    ExportacaoCandidatosProcesso,
    ExportacaoVagasProcesso,
    ExportacaoVagasSigpec,
)
from exporta_arquivo.models.exportacao_lote import (
    ExportacaoLote,
    StatusExportacao,
)


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

    @staticmethod
    def _salvar(
        instancia: ExportacaoLote, *, campos_atualizacao: list[str]
    ) -> None:
        """Persiste a instância usando update_fields."""
        instancia.save(update_fields=campos_atualizacao)

    @classmethod
    def marcar_atencao(
        cls,
        instancia: ExportacaoLote,
        *,
        conteudo_arquivo: str,
        nome_arquivo: str,
    ) -> None:
        """Marca a exportação como ATENCAO e persiste o arquivo de erro."""
        instancia.conteudo_arquivo = conteudo_arquivo
        instancia.nome_arquivo = nome_arquivo
        instancia.status = StatusExportacao.ATENCAO
        cls._salvar(
            instancia,
            campos_atualizacao=["conteudo_arquivo", "nome_arquivo", "status"],
        )

    @classmethod
    def marcar_sucesso(
        cls,
        instancia: ExportacaoLote,
        *,
        conteudo_arquivo: str,
        nome_arquivo: str,
    ) -> None:
        """Marca a exportação como SUCESSO e persiste o arquivo gerado."""
        instancia.conteudo_arquivo = conteudo_arquivo
        instancia.nome_arquivo = nome_arquivo
        instancia.status = StatusExportacao.SUCESSO
        cls._salvar(
            instancia,
            campos_atualizacao=["conteudo_arquivo", "nome_arquivo", "status"],
        )

    @classmethod
    def marcar_erro(cls, instancia: ExportacaoLote) -> None:
        """Marca a exportação como ERRO."""
        instancia.status = StatusExportacao.ERRO
        cls._salvar(instancia, campos_atualizacao=["status"])


class ExportacaoCandidatosProcessoRepository:
    """Persistência de registros de exportação de candidatos por processo."""

    @staticmethod
    def _salvar(
        instancia: ExportacaoCandidatosProcesso,
        *,
        campos_atualizacao: list[str],
    ) -> None:
        """Persiste a instância usando update_fields."""
        instancia.save(update_fields=campos_atualizacao)

    @classmethod
    def atualizar_dados_concurso(
        cls,
        instancia: ExportacaoCandidatosProcesso,
        *,
        concurso_codigo: int | None,
        concurso_data_criacao: Any,
    ) -> None:
        """Persiste código e data de criação do concurso vinculado."""
        instancia.concurso_codigo = concurso_codigo
        instancia.concurso_data_criacao = concurso_data_criacao
        cls._salvar(
            instancia,
            campos_atualizacao=["concurso_codigo", "concurso_data_criacao"],
        )

    @classmethod
    def atualizar_arquivo(
        cls,
        instancia: ExportacaoCandidatosProcesso,
        *,
        conteudo_arquivo: str,
        nome_arquivo: str,
    ) -> None:
        """Persiste o conteúdo e o nome do arquivo exportado."""
        instancia.conteudo_arquivo = conteudo_arquivo
        instancia.nome_arquivo = nome_arquivo
        cls._salvar(
            instancia, campos_atualizacao=["conteudo_arquivo", "nome_arquivo"]
        )


class ExportacaoVagasProcessoRepository:
    """Persistência de registros de exportação de vagas por processo."""

    @staticmethod
    def atualizar_arquivo(
        instancia: ExportacaoVagasProcesso,
        *,
        conteudo_arquivo: str,
        nome_arquivo: str,
    ) -> None:
        """Persiste o conteúdo e o nome do arquivo exportado."""
        instancia.conteudo_arquivo = conteudo_arquivo
        instancia.nome_arquivo = nome_arquivo
        instancia.save(update_fields=["conteudo_arquivo", "nome_arquivo"])


class ExportacaoVagasSigpecRepository:
    """Persistência de registros de exportação de vagas SIGPEC."""

    @staticmethod
    def atualizar_arquivo(
        instancia: ExportacaoVagasSigpec,
        *,
        conteudo_arquivo: str,
        nome_arquivo: str,
    ) -> None:
        """Persiste o conteúdo e o nome do arquivo exportado."""
        instancia.conteudo_arquivo = conteudo_arquivo
        instancia.nome_arquivo = nome_arquivo
        instancia.save(update_fields=["conteudo_arquivo", "nome_arquivo"])

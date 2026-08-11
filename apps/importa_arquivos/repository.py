"""Repositórios de acesso a dados do app importa_arquivos."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.contrib.contenttypes.models import ContentType

from importa_arquivos.models import (
    ImportacaoArquivoHabilitado,
    ImportacaoArquivoVagas,
    ImportacaoErro,
    ImportacaoEscolhas,
    ImportacaoLotes,
    LayoutArquivoImportacao,
    LogRequestHttp,
)
from importa_arquivos.serializers.importacao_erros import (
    ImportacaoErrosListSerializer,
)
from importa_arquivos.serializers.layout import (
    LayoutArquivoImportacaoSerializer,
)


class ImportacaoArquivoHabilitadoRepository:
    """Consultas e persistência de importações de habilitados."""

    @staticmethod
    def salvar(
        instancia: ImportacaoArquivoHabilitado,
        *,
        campos_atualizacao: list[str] | None = None,
    ) -> None:
        """Persiste a instância, usando update_fields quando informado."""
        if campos_atualizacao:
            instancia.save(update_fields=campos_atualizacao)
        else:
            instancia.save()

    @classmethod
    def atualizar_quantidade(
        cls, instancia: ImportacaoArquivoHabilitado, quantidade: int
    ) -> None:
        """Seta a quantidade de registros e salva."""
        instancia.quantidade = quantidade
        cls.salvar(instancia, campos_atualizacao=["quantidade"])

    @classmethod
    def atualizar_status(
        cls, instancia: ImportacaoArquivoHabilitado, status: str
    ) -> None:
        """Seta o status e salva."""
        instancia.status = status
        cls.salvar(instancia, campos_atualizacao=["status"])

    @staticmethod
    def recarregar(
        instancia: ImportacaoArquivoHabilitado,
    ) -> ImportacaoArquivoHabilitado:
        """Recarrega a instância a partir do banco."""
        instancia.refresh_from_db()
        return instancia


class ImportacaoArquivoVagasRepository:
    """Consultas e persistência de importações de vagas."""

    @staticmethod
    def salvar(
        instancia: ImportacaoArquivoVagas,
        *,
        campos_atualizacao: list[str] | None = None,
    ) -> None:
        """Persiste a instância, usando update_fields quando informado."""
        if campos_atualizacao:
            instancia.save(update_fields=campos_atualizacao)
        else:
            instancia.save()

    @classmethod
    def atualizar_status(
        cls, instancia: ImportacaoArquivoVagas, status: str
    ) -> None:
        """Seta o status e salva."""
        instancia.status = status
        cls.salvar(instancia, campos_atualizacao=["status"])

    @staticmethod
    def recarregar(
        instancia: ImportacaoArquivoVagas,
    ) -> ImportacaoArquivoVagas:
        """Recarrega a instância a partir do banco."""
        instancia.refresh_from_db()
        return instancia


class ImportacaoLotesRepository:
    """Consultas e persistência de importações de lotes de classificação."""

    @staticmethod
    def salvar(
        instancia: ImportacaoLotes,
        *,
        campos_atualizacao: list[str] | None = None,
    ) -> None:
        """Persiste a instância, usando update_fields quando informado."""
        if campos_atualizacao:
            instancia.save(update_fields=campos_atualizacao)
        else:
            instancia.save()

    @classmethod
    def concluir(
        cls,
        instancia: ImportacaoLotes,
        *,
        total_atualizados: int,
        detalhes: Any,
    ) -> None:
        """Marca status=CONCLUIDO e persiste total_atualizados/detalhes."""
        instancia.status = "CONCLUIDO"
        instancia.total_atualizados = total_atualizados
        instancia.detalhes = detalhes
        cls.salvar(
            instancia,
            campos_atualizacao=["status", "total_atualizados", "detalhes"],
        )

    @staticmethod
    def recarregar(instancia: ImportacaoLotes) -> ImportacaoLotes:
        """Recarrega a instância a partir do banco."""
        instancia.refresh_from_db()
        return instancia


class ImportacaoEscolhasRepository:
    """Consultas e persistência de importações de escolhas.

    ``criar`` retorna a instância (e não um dicionário, ao contrário do
    restante deste módulo), pois a view segue mutando/salvando esse mesmo
    objeto em múltiplos pontos subsequentes antes de qualquer serialização.
    """

    @staticmethod
    def serializar(instancia: ImportacaoEscolhas) -> dict[str, Any]:
        """Converte uma importação de escolhas em dicionário."""
        from importa_arquivos.serializers import (
            ImportacaoEscolhasListSerializer,
        )

        return ImportacaoEscolhasListSerializer(instancia).data

    @staticmethod
    def criar(**dados: Any) -> ImportacaoEscolhas:
        """Cria uma importação de escolhas."""
        return ImportacaoEscolhas.objects.create(**dados)

    @staticmethod
    def salvar(
        instancia: ImportacaoEscolhas,
        *,
        campos_atualizacao: list[str] | None = None,
    ) -> None:
        """Persiste a instância, usando update_fields quando informado."""
        if campos_atualizacao:
            instancia.save(update_fields=campos_atualizacao)
        else:
            instancia.save()

    @classmethod
    def atualizar_status(
        cls, instancia: ImportacaoEscolhas, status: str
    ) -> None:
        """Seta o status e salva."""
        instancia.status = status
        cls.salvar(instancia)

    @classmethod
    def atualizar_dados_prodam(
        cls, instancia: ImportacaoEscolhas, dados_prodam: Any
    ) -> None:
        """Seta dados_prodam e salva."""
        instancia.dados_prodam = dados_prodam
        cls.salvar(instancia, campos_atualizacao=["dados_prodam"])

    @staticmethod
    def recarregar(instancia: ImportacaoEscolhas) -> ImportacaoEscolhas:
        """Recarrega a instância a partir do banco."""
        instancia.refresh_from_db()
        return instancia


class LayoutArquivoImportacaoRepository:
    """Consultas de layouts de importação de arquivo."""

    @staticmethod
    def obter_por_tipo(tipo: str) -> dict[str, Any] | None:
        """Retorna o layout pelo tipo (o mais recente cadastrado) ou None."""
        layout = LayoutArquivoImportacao.objects.filter(tipo=tipo).first()
        if layout is None:
            return None
        return LayoutArquivoImportacaoSerializer(layout).data

    @staticmethod
    def obter_mais_recente_por_tipo(tipo: str) -> dict[str, Any] | None:
        """Retorna o layout ativo (mais recente) pelo tipo ou None."""
        layout = (
            LayoutArquivoImportacao.objects.filter(tipo=tipo)
            .order_by("-criado_em")
            .first()
        )
        if layout is None:
            return None
        return LayoutArquivoImportacaoSerializer(layout).data


class ImportacaoErroRepository:
    """Consultas e persistência de erros de importação."""

    @staticmethod
    def serializar_lista(erros: Any) -> list[dict[str, Any]]:
        """Converte uma lista/queryset de erros em dicionários."""
        return ImportacaoErrosListSerializer(erros, many=True).data

    @classmethod
    def listar_por_modelo_e_uuid(
        cls, model_cls: type, importacao_uuid: str | UUID | None = None
    ) -> list[dict[str, Any]]:
        """Lista erros filtrados por modelo de importação e UUID, já
        serializados.
        """
        content_type = ContentType.objects.get_for_model(model_cls)
        queryset = ImportacaoErro.objects.filter(
            content_type=content_type
        ).select_related("content_type")
        if importacao_uuid:
            queryset = queryset.filter(object_id=importacao_uuid)
        return cls.serializar_lista(queryset)

    @staticmethod
    def criar(
        *,
        importacao_obj: Any,
        mensagem: str,
        erros: str,
    ) -> ImportacaoErro:
        """Cria um registro de erro vinculado ao objeto de importação."""
        content_type = ContentType.objects.get_for_model(
            importacao_obj.__class__
        )
        return ImportacaoErro.objects.create(
            content_type=content_type,
            object_id=getattr(importacao_obj, "uuid", importacao_obj.id),
            mensagem=mensagem,
            erros=erros,
        )


class LogRequestHttpRepository:
    """Persistência de logs de requisições HTTP."""

    @staticmethod
    def criar(
        *,
        url: str,
        metodo_http: str,
        processo_id: int | None,
        resposta_raw: str,
    ) -> LogRequestHttp:
        """Cria um registro de log de requisição HTTP."""
        return LogRequestHttp.objects.create(
            url=url,
            metodo_http=metodo_http,
            processo_id=processo_id,
            resposta_raw=resposta_raw,
        )

"""Repositórios de acesso a dados do app importa_arquivos."""

from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)


class ImportacaoArquivoHabilitadoRepository:
    """Consultas e persistência de importações de habilitados."""

    @classmethod
    def atualizar(
        cls, instancia: ImportacaoArquivoHabilitado, **campos: Any
    ) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))

    @staticmethod
    def recarregar(
        instancia: ImportacaoArquivoHabilitado,
    ) -> ImportacaoArquivoHabilitado:
        """Recarrega a instância a partir do banco."""
        instancia.refresh_from_db()
        return instancia


class ImportacaoArquivoVagasRepository:
    """Consultas e persistência de importações de vagas."""

    @classmethod
    def atualizar(
        cls, instancia: ImportacaoArquivoVagas, **campos: Any
    ) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))

    @staticmethod
    def recarregar(
        instancia: ImportacaoArquivoVagas,
    ) -> ImportacaoArquivoVagas:
        """Recarrega a instância a partir do banco."""
        instancia.refresh_from_db()
        return instancia


class ImportacaoLotesRepository:
    """Consultas e persistência de importações de lotes de classificação."""

    @classmethod
    def atualizar(cls, instancia: ImportacaoLotes, **campos: Any) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))

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
        """Serializa uma importação de escolhas em dicionário."""
        from importa_arquivos.serializers import (
            ImportacaoEscolhasListSerializer,
        )

        return ImportacaoEscolhasListSerializer(instancia).data

    @staticmethod
    def criar(**dados: Any) -> ImportacaoEscolhas:
        """Cria uma importação de escolhas."""
        logger.info(
            f"Criando importação de escolhas:",
            extra={
                "dados": dados,
            }
        )
        return ImportacaoEscolhas.objects.create(**dados)

    @classmethod
    def atualizar(cls, instancia: ImportacaoEscolhas, **campos: Any) -> None:
        """Atualiza os campos informados na instância e persiste."""
        logger.info(
            f"Atualizando importação de escolhas:",
            extra={
                "instancia": instancia,
                "campos": campos,
            }
        )
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))

    @staticmethod
    def recarregar(instancia: ImportacaoEscolhas) -> ImportacaoEscolhas:
        """Recarrega a instância a partir do banco."""
        instancia.refresh_from_db()
        return instancia

    @staticmethod
    def listar_processos_distintos() -> list[dict[str, Any]]:
        """Retorna processo/concurso distintos já importados.

        Returns:
            Lista de dicionários com processo_uuid, processo_id e
            concurso_uuid.
        """
        vistos: set[tuple[Any, Any, Any]] = set()
        processos: list[dict[str, Any]] = []
        queryset = (
            ImportacaoEscolhas.objects.exclude(processo_uuid__isnull=True)
            .exclude(concurso_uuid__isnull=True)
            .values("processo_uuid", "processo_id", "concurso_uuid")
        )
        for item in queryset:
            chave = (
                item["processo_uuid"],
                item["processo_id"],
                item["concurso_uuid"],
            )
            if chave in vistos:
                continue
            vistos.add(chave)
            processos.append(item)
        return processos

    @staticmethod
    def existe_sucesso(
        processo_uuid: Any,
        processo_id: Any,
    ) -> bool:
        """Indica se já existe importação concluída para o processo.

        Args:
            processo_uuid: UUID do processo de convocação.
            processo_id: Identificador numérico usado na API PRODAM.

        Returns:
            ``True`` se houver registro com status ``CONCLUIDO``.
        """
        logger.info(
            f"Verificando se já existe importação concluída para o processo:",
            extra={
                "processo_uuid": processo_uuid,
                "processo_id": processo_id,
            }
        )
        return ImportacaoEscolhas.objects.filter(
            processo_uuid=processo_uuid,
            processo_id=processo_id,
            status="CONCLUIDO",
        ).exists()


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
        """Serializa uma lista/queryset de erros em dicionários."""
        return ImportacaoErrosListSerializer(erros, many=True).data

    @classmethod
    def listar_por_modelo_e_uuid(
        cls, model_cls: type, importacao_uuid: str | UUID | None = None
    ) -> list[dict[str, Any]]:
        """Lista erros filtrados por modelo de importação e UUID.

        Já serializados.
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

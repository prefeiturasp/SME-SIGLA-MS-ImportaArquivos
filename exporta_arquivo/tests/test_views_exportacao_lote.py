"""Testes de ExportacaoLoteViewSet e CabecalhoExportacaoLoteViewSet.

Cobre:
- create: sucesso (200 + arquivo), ExportacaoLoteIncompletaException (422),
outras exceções (400)
- download: com arquivo (200), sem arquivo (404)
- list: 200 paginado, filtros básicos
- retrieve: 200 com campos corretos
- _gerar_conteudo_erro: geração de mensagem de erro
- CabecalhoExportacaoLoteViewSet: list e create
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from exporta_arquivo.models import CabecalhoExportacaoLote, ExportacaoLote
from exporta_arquivo.services.exceptions import (
    ExportacaoBadRequestException,
    ExportacaoLoteIncompletaException,
)
from exporta_arquivo.views.exportacao_lote import ExportacaoLoteViewSet

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.urls("exporta_arquivo.tests.urls"),
]
LOTE_URL = "/api/v1/exportacao/lote/"
CABECALHO_URL = "/api/v1/exportacao/cabecalho-lote/"


def _uuid() -> Any:
    """Executa  uuid."""
    return str(uuid.uuid4())


@pytest.fixture
def api_client() -> Any:
    """Executa api client."""
    return APIClient()


@pytest.fixture
def payload_valido() -> Any:
    """Executa payload valido."""
    return {
        "concurso_uuid": _uuid(),
        "concurso_nome": "Concurso SME 2024",
        "numero_lote": 3,
        "lote_uuid": _uuid(),
    }


@pytest.fixture
def registro_exportado() -> Any:
    """Executa registro exportado."""
    return ExportacaoLote.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso X",
        numero_lote=1,
        lote_uuid=uuid.uuid4(),
        conteudo_arquivo="@TABELA=...\n1;SIG;123;15062024;S;ESCOLA01;\n",
        nome_arquivo="exportacao_lote_1.txt",
        status="SUCESSO",
    )


class TestExportacaoLoteCreate:
    """POST /exportacao/lote/."""

    def test_sucesso_retorna_200_e_arquivo_txt(
        self, api_client: Any, payload_valido: Any
    ) -> None:
        """Verifica sucesso retorna 200 e arquivo txt."""
        conteudo = "@TABELA=...\n1;SIG;999;15062024;S;ESCOLA;\n"
        with patch(
            "exporta_arquivo.views.exportacao_lote.exportar_lote",
            return_value=conteudo,
        ):
            response = api_client.post(LOTE_URL, payload_valido, format="json")
        assert response.status_code == 200
        assert "text/plain" in response.get("Content-Type", "")
        assert "attachment" in response.get("Content-Disposition", "")
        assert "exportacao_lote_" in response.get("Content-Disposition", "")

    def test_sucesso_persiste_status_sucesso_e_conteudo(
        self, api_client: Any, payload_valido: Any
    ) -> None:
        """Verifica sucesso persiste status sucesso e conteudo."""
        conteudo = "@TABELA=...\n1;SIG;999;15062024;S;ESCOLA;\n"
        with patch(
            "exporta_arquivo.views.exportacao_lote.exportar_lote",
            return_value=conteudo,
        ):
            api_client.post(LOTE_URL, payload_valido, format="json")
        registro = ExportacaoLote.objects.order_by("-criado_em").first()
        assert registro.status == "SUCESSO"  # type: ignore[union-attr]
        assert registro.conteudo_arquivo == conteudo  # type: ignore[union-attr]
        assert registro.nome_arquivo.startswith("exportacao_lote_")  # type: ignore[union-attr]
        assert registro.nome_arquivo.endswith(".txt")  # type: ignore[union-attr]

    def test_incompleto_retorna_422_e_arquivo_de_erro(
        self, api_client: Any, payload_valido: Any
    ) -> None:
        """Verifica incompleto retorna 422 e arquivo de erro."""
        exc = ExportacaoLoteIncompletaException(
            candidatos_sem_escolha=["Pedro", "Ana"]
        )
        with patch(
            "exporta_arquivo.views.exportacao_lote.exportar_lote",
            side_effect=exc,
        ):
            response = api_client.post(LOTE_URL, payload_valido, format="json")
        assert response.status_code == 422
        assert "text/plain" in response.get("Content-Type", "")
        conteudo = response.content.decode("utf-8")
        assert "Pedro" in conteudo
        assert "Ana" in conteudo

    def test_incompleto_persiste_status_atencao(
        self, api_client: Any, payload_valido: Any
    ) -> None:
        """Verifica incompleto persiste status atencao."""
        exc = ExportacaoLoteIncompletaException(
            candidatos_sem_escolha=["Carlos"]
        )
        with patch(
            "exporta_arquivo.views.exportacao_lote.exportar_lote",
            side_effect=exc,
        ):
            api_client.post(LOTE_URL, payload_valido, format="json")
        registro = ExportacaoLote.objects.order_by("-criado_em").first()
        assert registro.status == "ATENCAO"  # type: ignore[union-attr]
        assert "Carlos" in registro.conteudo_arquivo  # type: ignore[operator,union-attr]
        assert "candidatos_sem_escolha_lote_" in registro.nome_arquivo  # type: ignore[operator,union-attr]

    def test_excecao_generica_retorna_400_e_persiste_status_erro(
        self, api_client: Any, payload_valido: Any
    ) -> None:
        """Verifica excecao generica retorna 400 e persiste status erro."""
        exc = ExportacaoBadRequestException(
            mensagem="Parâmetro inválido.", detalhes="numero_lote"
        )
        with patch(
            "exporta_arquivo.views.exportacao_lote.exportar_lote",
            side_effect=exc,
        ):
            response = api_client.post(LOTE_URL, payload_valido, format="json")
        assert response.status_code == 400
        data = response.json()
        assert "mensagem" in data
        registro = ExportacaoLote.objects.order_by("-criado_em").first()
        assert registro.status == "ERRO"  # type: ignore[union-attr]

    def test_serializer_invalido_retorna_400(self, api_client: Any) -> None:
        """Verifica serializer invalido retorna 400."""
        response = api_client.post(LOTE_URL, {}, format="json")
        assert response.status_code == 400

    def test_nome_arquivo_usa_numero_lote(
        self, api_client: Any, payload_valido: Any
    ) -> None:
        """Verifica nome arquivo usa numero lote."""
        conteudo = "@TABELA=...\n"
        with patch(
            "exporta_arquivo.views.exportacao_lote.exportar_lote",
            return_value=conteudo,
        ):
            response = api_client.post(LOTE_URL, payload_valido, format="json")
        assert "3" in response.get("Content-Disposition", "")


class TestExportacaoLoteDownload:
    """GET /exportacao/lote/<uuid>/download/."""

    def test_com_arquivo_retorna_200_e_conteudo(
        self, api_client: Any, registro_exportado: Any
    ) -> None:
        """Verifica com arquivo retorna 200 e conteudo."""
        url = f"{LOTE_URL}{registro_exportado.uuid}/download/"
        response = api_client.get(url)
        assert response.status_code == 200
        assert b"@TABELA=" in response.content
        assert "attachment" in response.get("Content-Disposition", "")
        assert registro_exportado.nome_arquivo in response.get(
            "Content-Disposition", ""
        )

    def test_sem_arquivo_retorna_404(self, api_client: Any) -> None:
        """Verifica sem arquivo retorna 404."""
        registro = ExportacaoLote.objects.create(
            concurso_uuid=uuid.uuid4(),
            concurso_nome="Sem Arquivo",
            numero_lote=99,
            lote_uuid=uuid.uuid4(),
        )
        url = f"{LOTE_URL}{registro.uuid}/download/"
        response = api_client.get(url)
        assert response.status_code == 404

    def test_uuid_inexistente_retorna_404(self, api_client: Any) -> None:
        """Verifica uuid inexistente retorna 404."""
        url = f"{LOTE_URL}{_uuid()}/download/"
        response = api_client.get(url)
        assert response.status_code == 404


class TestExportacaoLoteList:
    """GET /exportacao/lote/."""

    def test_lista_paginada_retorna_200(self, api_client: Any) -> None:
        """Verifica lista paginada retorna 200."""
        ExportacaoLote.objects.create(
            concurso_uuid=uuid.uuid4(),
            concurso_nome="A",
            numero_lote=1,
            lote_uuid=uuid.uuid4(),
        )
        response = api_client.get(LOTE_URL)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data

    def test_lista_retorna_campos_do_list_serializer(
        self, api_client: Any, registro_exportado: Any
    ) -> None:
        """Verifica lista retorna campos do list serializer."""
        response = api_client.get(LOTE_URL)
        assert response.status_code == 200
        item = response.json()["results"][0]
        for campo in (
            "uuid",
            "criado_em",
            "atualizado_em",
            "concurso_uuid",
            "concurso_nome",
            "numero_lote",
            "lote_uuid",
            "nome_arquivo",
            "status",
        ):
            assert campo in item

    def test_filtro_por_numero_lote(self, api_client: Any) -> None:
        """Verifica filtro por numero lote."""
        ExportacaoLote.objects.create(
            concurso_uuid=uuid.uuid4(),
            concurso_nome="B",
            numero_lote=77,
            lote_uuid=uuid.uuid4(),
        )
        ExportacaoLote.objects.create(
            concurso_uuid=uuid.uuid4(),
            concurso_nome="C",
            numero_lote=88,
            lote_uuid=uuid.uuid4(),
        )
        response = api_client.get(LOTE_URL, {"numero_lote": 77})
        assert response.status_code == 200
        results = response.json()["results"]
        assert all(r["numero_lote"] == 77 for r in results)


class TestExportacaoLoteRetrieve:
    """GET /exportacao/lote/<uuid>/."""

    def test_retrieve_retorna_200_com_campos(
        self, api_client: Any, registro_exportado: Any
    ) -> None:
        """Verifica retrieve retorna 200 com campos."""
        url = f"{LOTE_URL}{registro_exportado.uuid}/"
        response = api_client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert str(data["uuid"]) == str(registro_exportado.uuid)
        assert data["status"] == "SUCESSO"

    def test_retrieve_uuid_inexistente_retorna_404(
        self, api_client: Any
    ) -> None:
        """Verifica retrieve uuid inexistente retorna 404."""
        response = api_client.get(f"{LOTE_URL}{_uuid()}/")
        assert response.status_code == 404


class TestGerarConteudoErro:
    """ExportacaoLoteViewSet._gerar_conteudo_erro (método estático)."""

    def test_inclui_nome_do_lote_e_candidatos(self) -> None:
        """Verifica inclui nome do lote e candidatos."""
        instance = ExportacaoLote(numero_lote=5, lote_uuid=uuid.uuid4())
        out = ExportacaoLoteViewSet._gerar_conteudo_erro(
            ["João", "Maria"], instance
        )
        assert "lote 5" in out.lower() or "5" in out
        assert "- João" in out
        assert "- Maria" in out

    def test_usa_lote_uuid_quando_numero_lote_none(self) -> None:
        """Verifica usa lote uuid quando numero lote none."""
        lote_uuid = uuid.uuid4()
        instance = ExportacaoLote(numero_lote=None, lote_uuid=lote_uuid)  # type: ignore[misc]
        out = ExportacaoLoteViewSet._gerar_conteudo_erro(["Carlos"], instance)
        assert str(lote_uuid) in out

    def test_termina_com_newline(self) -> None:
        """Verifica termina com newline."""
        instance = ExportacaoLote(numero_lote=1, lote_uuid=uuid.uuid4())
        out = ExportacaoLoteViewSet._gerar_conteudo_erro(["X"], instance)
        assert out.endswith("\n")


class TestCabecalhoExportacaoLoteViewSet:
    """CRUD do cabeçalho de exportação de lotes."""

    def test_list_vazia_retorna_200(self, api_client: Any) -> None:
        """Verifica list vazia retorna 200."""
        response = api_client.get(CABECALHO_URL)
        assert response.status_code == 200

    def test_create_retorna_201_com_campos(self, api_client: Any) -> None:
        """Verifica create retorna 201 com campos."""
        payload = {
            "tabela": "[c_ERGON][TESTE][1.0]",
            "chave": "[ID][NUMBER]",
            "separador": ";",
            "formato_data": "DD/MM/YYYY",
            "colunas": "[ID][NUMBER]",
            "ativo": True,
        }
        response = api_client.post(CABECALHO_URL, payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["tabela"] == "[c_ERGON][TESTE][1.0]"
        assert "uuid" in data

    def test_partial_update_altera_campo(self, api_client: Any) -> None:
        """Verifica partial update altera campo."""
        cabecalho = CabecalhoExportacaoLote.objects.create()
        url = f"{CABECALHO_URL}{cabecalho.uuid}/"
        response = api_client.patch(url, {"separador": "|"}, format="json")
        assert response.status_code == 200
        assert response.json()["separador"] == "|"

    def test_filtro_ativo_false_retorna_apenas_inativos(
        self, api_client: Any
    ) -> None:
        """Verifica filtro ativo false retorna apenas inativos."""
        CabecalhoExportacaoLote.objects.create(ativo=True)
        CabecalhoExportacaoLote.objects.create(ativo=False)
        response = api_client.get(CABECALHO_URL, {"ativo": "false"})
        assert response.status_code == 200
        data = response.json()
        results = data if isinstance(data, list) else data.get("results", data)
        assert len(results) >= 1
        assert all(not r["ativo"] for r in results)

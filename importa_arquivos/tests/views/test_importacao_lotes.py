"""Testes do ImportacaoLotesViewSet:.

- create: sucesso (201), ErrosValidacaoLotesException (400),
BaseImportacaoException (400),
          exceção genérica (400), falha na API de candidatos (400), serializer
          inválido (400)
- list: 200 paginado, filtro por status
- retrieve: 200 e 404
- get_serializer_class: create usa Create, list/retrieve usa List.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from importa_arquivos.models import ImportacaoLotes
from importa_arquivos.services.exceptions import (
    ArquivoLotesVazioException,
    ErrosValidacaoLotesException,
    ImportacaoServiceUnavailableException,
)

pytestmark = pytest.mark.django_db
LOTES_LIST_URL = "/api/v1/importacao/lotes/"
HEADER = "LOTE;EMPRESA;VAGA;IDENTIFICACAO;CHAVE_INSCRITO;NUMFUNC;NUMVINC\n"


def _txt_valido(lote: Any = 1) -> Any:
    """Executa  txt valido."""
    linha = f"{lote};EMP01;VAGA01;100;CH01;999;1\n"
    return (HEADER + linha).encode("utf-8")


def _arquivo(conteudo: bytes = None, nome: Any = "lotes.txt") -> Any:  # type: ignore[assignment]
    """Executa  arquivo."""
    return SimpleUploadedFile(
        nome, conteudo or _txt_valido(), content_type="text/plain"
    )


def _payload(arquivo: Any = None, concurso_uuid: Any = None) -> Any:
    """Executa  payload."""
    return {
        "arquivo": arquivo or _arquivo(),
        "concurso_uuid": str(concurso_uuid or uuid.uuid4()),
        "concurso_nome": "Concurso SME 2024",
    }


def _registros_validos() -> Any:
    """Executa  registros validos."""
    return [
        {
            "lote": 1,
            "empresa": "EMP01",
            "vaga": "VAGA01",
            "identificacao": 100,
            "chave_inscrito": "CH01",
            "numfunc": 999,
            "numvinc": 1,
        }
    ]


class TestImportacaoLotesCreate:
    """POST /api/v1/importacao/lotes/."""

    def test_sucesso_retorna_201_e_status_concluido(
        self, api_client: Any
    ) -> None:
        """Verifica sucesso retorna 201 e status concluido."""
        with (
            patch(
                "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
                return_value=_registros_validos(),
            ),
            patch(
                "importa_arquivos.views.importacao_lotes.ApiCandidatosService"
            ) as MockApi,
        ):
            MockApi.return_value.salvar_lotes.return_value = 1
            resp = api_client.post(
                LOTES_LIST_URL, _payload(), format="multipart"
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "CONCLUIDO"
        assert data["total_atualizados"] == 1

    def test_sucesso_persiste_detalhes_e_total(self, api_client: Any) -> None:
        """Verifica sucesso persiste detalhes e total."""
        registros = _registros_validos()
        with (
            patch(
                "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
                return_value=registros,
            ),
            patch(
                "importa_arquivos.views.importacao_lotes.ApiCandidatosService"
            ) as MockApi,
        ):
            MockApi.return_value.salvar_lotes.return_value = 3
            api_client.post(LOTES_LIST_URL, _payload(), format="multipart")
        registro = ImportacaoLotes.objects.order_by("-criado_em").first()
        assert registro.status == "CONCLUIDO"  # type: ignore[union-attr]
        assert registro.total_atualizados == 3  # type: ignore[union-attr]
        assert registro.detalhes == registros  # type: ignore[union-attr]

    def test_erros_validacao_retorna_400(self, api_client: Any) -> None:
        """Verifica erros validacao retorna 400."""
        exc = ErrosValidacaoLotesException(
            mensagem="Erro ao validar.", detalhes="Linha 2: lote inválido."
        )
        with patch(
            "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
            side_effect=exc,
        ):
            resp = api_client.post(
                LOTES_LIST_URL, _payload(), format="multipart"
            )
        assert resp.status_code == 400
        data = resp.json()
        assert "mensagem" in data
        assert "Erro ao validar" in data["mensagem"]

    def test_base_importacao_exception_retorna_400(
        self, api_client: Any
    ) -> None:
        """Verifica base importacao exception retorna 400."""
        exc = ArquivoLotesVazioException(mensagem="Arquivo vazio.")
        with patch(
            "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
            side_effect=exc,
        ):
            resp = api_client.post(
                LOTES_LIST_URL, _payload(), format="multipart"
            )
        assert resp.status_code == 400
        data = resp.json()
        assert "mensagem" in data

    def test_excecao_generica_na_validacao_retorna_400(
        self, api_client: Any
    ) -> None:
        """Verifica excecao generica na validacao retorna 400."""
        with patch(
            "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
            side_effect=RuntimeError("boom"),
        ):
            resp = api_client.post(
                LOTES_LIST_URL, _payload(), format="multipart"
            )
        assert resp.status_code == 400
        data = resp.json()
        assert "mensagem" in data

    def test_api_candidatos_falha_retorna_400(self, api_client: Any) -> None:
        """Verifica api candidatos falha retorna 400."""
        with (
            patch(
                "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
                return_value=_registros_validos(),
            ),
            patch(
                "importa_arquivos.views.importacao_lotes.ApiCandidatosService"
            ) as MockApi,
        ):
            MockApi.return_value.salvar_lotes.side_effect = (
                ImportacaoServiceUnavailableException(
                    mensagem="Serviço indisponível."
                )
            )
            resp = api_client.post(
                LOTES_LIST_URL, _payload(), format="multipart"
            )
        assert resp.status_code == 400
        data = resp.json()
        assert "mensagem" in data

    def test_serializer_invalido_sem_concurso_uuid_retorna_400(
        self, api_client: Any
    ) -> None:
        """Verifica serializer invalido sem concurso uuid retorna 400."""
        resp = api_client.post(
            LOTES_LIST_URL, {"arquivo": _arquivo()}, format="multipart"
        )
        assert resp.status_code == 400

    def test_serializer_invalido_sem_arquivo_retorna_400(
        self, api_client: Any
    ) -> None:
        """Verifica serializer invalido sem arquivo retorna 400."""
        resp = api_client.post(
            LOTES_LIST_URL,
            {"concurso_uuid": str(uuid.uuid4())},
            format="multipart",
        )
        assert resp.status_code == 400

    def test_salvar_lotes_chamado_com_concurso_uuid_e_registros(
        self, api_client: Any
    ) -> None:
        """Verifica salvar lotes chamado com concurso uuid e registros."""
        concurso_uuid = uuid.uuid4()
        registros = _registros_validos()
        with (
            patch(
                "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
                return_value=registros,
            ),
            patch(
                "importa_arquivos.views.importacao_lotes.ApiCandidatosService"
            ) as MockApi,
        ):
            MockApi.return_value.salvar_lotes.return_value = 1
            api_client.post(
                LOTES_LIST_URL,
                _payload(concurso_uuid=concurso_uuid),
                format="multipart",
            )
        MockApi.return_value.salvar_lotes.assert_called_once()
        call_kwargs = MockApi.return_value.salvar_lotes.call_args.kwargs
        assert call_kwargs["concurso_uuid"] == str(concurso_uuid)
        assert call_kwargs["lotes"] == registros


class TestImportacaoLotesList:
    """GET /api/v1/importacao/lotes/."""

    def test_lista_vazia_retorna_200_paginado(self, api_client: Any) -> None:
        """Verifica lista vazia retorna 200 paginado."""
        resp = api_client.get(LOTES_LIST_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "count" in data

    def test_lista_com_registros_retorna_campos_corretos(
        self, api_client: Any
    ) -> None:
        """Verifica lista com registros retorna campos corretos."""
        ImportacaoLotes.objects.create(
            nome_arquivo="lotes.txt",
            arquivo=SimpleUploadedFile("lotes.txt", b"x"),
            tipo="LOTES",
            status="CONCLUIDO",
            concurso_uuid=uuid.uuid4(),
        )
        resp = api_client.get(LOTES_LIST_URL)
        assert resp.status_code == 200
        item = resp.json()["results"][0]
        for campo in (
            "uuid",
            "nome_arquivo",
            "status",
            "concurso_uuid",
            "criado_em",
        ):
            assert campo in item

    def test_filtro_por_status(self, api_client: Any) -> None:
        """Verifica filtro por status."""
        ImportacaoLotes.objects.create(
            nome_arquivo="a.txt",
            arquivo=SimpleUploadedFile("a.txt", b"x"),
            tipo="LOTES",
            status="CONCLUIDO",
            concurso_uuid=uuid.uuid4(),
        )
        ImportacaoLotes.objects.create(
            nome_arquivo="b.txt",
            arquivo=SimpleUploadedFile("b.txt", b"x"),
            tipo="LOTES",
            status="ERRO",
            concurso_uuid=uuid.uuid4(),
        )
        resp = api_client.get(LOTES_LIST_URL, {"status": "ERRO"})
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert all(r["status"] == "ERRO" for r in results)


class TestImportacaoLotesRetrieve:
    """GET /api/v1/importacao/lotes/<uuid>/."""

    def test_retrieve_existente_retorna_200(self, api_client: Any) -> None:
        """Verifica retrieve existente retorna 200."""
        reg = ImportacaoLotes.objects.create(
            nome_arquivo="x.txt",
            arquivo=SimpleUploadedFile("x.txt", b"x"),
            tipo="LOTES",
            status="CONCLUIDO",
            concurso_uuid=uuid.uuid4(),
        )
        resp = api_client.get(f"{LOTES_LIST_URL}{reg.uuid}/")
        assert resp.status_code == 200
        assert str(resp.json()["uuid"]) == str(reg.uuid)

    def test_retrieve_inexistente_retorna_404(self, api_client: Any) -> None:
        """Verifica retrieve inexistente retorna 404."""
        resp = api_client.get(f"{LOTES_LIST_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404


class TestImportacaoLotesGetSerializerClass:
    """get_serializer_class: POST usa Create, GET list/retrieve usa List."""

    def test_get_list_usa_list_serializer(self, api_client: Any) -> None:
        """Verifica get list usa list serializer."""
        from importa_arquivos.serializers import ImportacaoLotesListSerializer

        resp = api_client.get(LOTES_LIST_URL)
        assert resp.status_code == 200
        if resp.json()["results"]:
            resp.json()["results"][0]
            list_fields = set(ImportacaoLotesListSerializer.Meta.fields)
            for campo in ("uuid", "status", "nome_arquivo"):
                assert campo in list_fields

    def test_post_create_usa_create_serializer(self, api_client: Any) -> None:
        """Verifica post create usa create serializer."""
        with (
            patch(
                "importa_arquivos.views.importacao_lotes.validar_txt_lotes",
                return_value=_registros_validos(),
            ),
            patch(
                "importa_arquivos.views.importacao_lotes.ApiCandidatosService"
            ) as MockApi,
        ):
            MockApi.return_value.salvar_lotes.return_value = 0
            resp = api_client.post(
                LOTES_LIST_URL, _payload(), format="multipart"
            )
        assert resp.status_code == 201

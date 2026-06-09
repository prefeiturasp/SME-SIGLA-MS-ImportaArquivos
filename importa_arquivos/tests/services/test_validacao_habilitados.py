"""Módulo tests/services/test_validacao_habilitados."""

from __future__ import annotations

import io
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from importa_arquivos.models import LayoutArquivoImportacao
from importa_arquivos.services.exceptions import (
    CargoConcursoInvalidoException,
    ColunaCSVInvalidaException,
    LayoutNaoConfiguradoException,
)
from importa_arquivos.services.validacao_habilitados import (
    validar_csv_habilitados,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def layout_com_cargo() -> None:
    """Executa layout com cargo."""
    estrutura = [
        {
            "coluna": "Inscricao",
            "campo_payload": "codigo_inscricao",
            "obrigatorio": "1",
        },
        {"coluna": "Nome", "campo_payload": "nome", "obrigatorio": "1"},
        {"coluna": "CPF", "campo_payload": "cpf", "obrigatorio": "1"},
        {
            "coluna": "Codigo_do_Cargo",
            "campo_payload": "codigo_cargo",
            "obrigatorio": "1",
        },
    ]
    LayoutArquivoImportacao.objects.create(
        tipo="HABILITADOS", estrutura=estrutura
    )


def test_validar_csv_habilitados_sucesso(layout_habilitados: Any) -> None:
    """Verifica validar csv habilitados sucesso."""
    csv = "CPF\n17888214088\n"
    arquivo = SimpleUploadedFile(
        "h.csv", csv.encode("utf-8-sig"), content_type="text/csv"
    )
    registros, estrutura = validar_csv_habilitados(arquivo)
    assert len(registros) == 1
    assert registros[0]["CPF"] == "17888214088"
    assert isinstance(estrutura, list)


def test_validar_csv_habilitados_sem_layout() -> None:
    """Verifica validar csv habilitados sem layout."""
    arquivo = SimpleUploadedFile(
        "h.csv", b"CPF\n123\n", content_type="text/csv"
    )
    with pytest.raises(LayoutNaoConfiguradoException):
        validar_csv_habilitados(arquivo)


def _criar_layout_minimo() -> None:
    """Executa  criar layout minimo."""
    estrutura = [
        {
            "coluna": "Inscricao",
            "campo_payload": "codigo_inscricao",
            "obrigatorio": 1,
        },
        {"coluna": "Nome", "campo_payload": "nome", "obrigatorio": 1},
        {
            "coluna": "DataNascimento",
            "campo_payload": "data_nascimento",
            "obrigatorio": 0,
        },
        {"coluna": "CPF", "campo_payload": "cpf", "obrigatorio": 1},
        {"coluna": "Email", "campo_payload": "email", "obrigatorio": 0},
    ]
    LayoutArquivoImportacao.objects.create(
        tipo="HABILITADOS", estrutura=estrutura
    )


def _csv_bytes(text: str) -> io.BytesIO:
    """Executa  csv bytes."""
    return io.BytesIO(text.encode("utf-8"))


def test_validacao_sucesso_minimo() -> None:
    """Verifica validacao sucesso minimo."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n00000001,Fulano,05/29/1990,39053344705,fulano@example.com\n"  # noqa: E501
    registros, _ = validar_csv_habilitados(_csv_bytes(csv_text))
    assert len(registros) == 1 and registros[0]["Nome"] == "Fulano"


def test_obrigatorios_agrupados_mesma_linha() -> None:
    """Verifica obrigatorios agrupados mesma linha."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n,,05/29/1990,,valid@example.com\n"  # noqa: E501
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert "Linha 2" in exc.value.detalhes
    assert "Campos obrigatórios vazios" in exc.value.detalhes
    assert "Nome" in exc.value.detalhes and "CPF" in exc.value.detalhes


def test_email_invalido_agregado() -> None:
    """Verifica email invalido agregado."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n1,Fulano,05/29/1990,39053344705,foo@bar\n"  # noqa: E501
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert (
        "Linha 2" in exc.value.detalhes
        and "Email inválido" in exc.value.detalhes
    )


def test_cpf_invalido_agregado() -> None:
    """Verifica cpf invalido agregado."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n1,Fulano,05/29/1990,12345678900,fulano@example.com\n"  # noqa: E501
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert (
        "Linha 2" in exc.value.detalhes
        and "CPF inválido" in exc.value.detalhes
    )


def test_data_nascimento_invalida_agregada() -> None:
    """Verifica data nascimento invalida agregada."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n1,Fulano,29/05/1990,39053344705,fulano@example.com\n"  # noqa: E501
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert (
        "Linha 2" in exc.value.detalhes
        and "dataNascimento inválida" in exc.value.detalhes
    )


def test_erros_agregados_mesma_linha() -> None:
    """Verifica erros agregados mesma linha."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n1,,05/29/1990,12345678900,foo@bar\n"  # noqa: E501
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    detalhes = exc.value.detalhes
    assert "Linha 2" in detalhes
    assert "Campos obrigatórios vazios" in detalhes and "Nome" in detalhes
    assert "Email inválido" in detalhes and "CPF inválido" in detalhes


def test_email_duplicado_com_mesmo_cpf_ok() -> None:
    """Verifica email duplicado com mesmo cpf ok."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n1,Fulano,05/29/1990,39053344705,dup@example.com\n2,Ciclano,05/29/1990,39053344705,dup@example.com\n"  # noqa: E501
    registros, _ = validar_csv_habilitados(_csv_bytes(csv_text))
    assert len(registros) == 2


def test_email_duplicado_com_cpfs_diferentes_erro_mensagem_linhas_divergentes() -> (  # noqa: E501
    None
):
    """Verifica email duplicado com cpfs diferentes erro mensagem linhas."""
    _criar_layout_minimo()
    csv_text = "Inscricao,Nome,DataNascimento,CPF,Email\n1,Fulano,05/29/1990,39053344705,dup@example.com\n2,Ciclano,05/29/1990,17888214088,dup@example.com\n"  # noqa: E501
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    detalhes = exc.value.detalhes
    assert "Linha 3" in detalhes
    assert (
        "Email duplicado. CPF 17888214088 com o mesmo email que o CPF 39053344705"  # noqa: E501
        in detalhes
    )


from importa_arquivos.services.validacao_habilitados import (
    _validar_codigo_cargo,
)

COLUNAS_COM_CARGO = {
    "email_col": None,
    "cpf_col": None,
    "dn_col": None,
    "cargo_col": "Codigo_do_Cargo",
    "obrigatorias": ["Codigo_do_Cargo", "Nome"],
}
COLUNAS_SEM_CARGO = {
    "email_col": None,
    "cpf_col": None,
    "dn_col": None,
    "cargo_col": None,
    "obrigatorias": ["Nome"],
}


def test_validar_codigo_cargo_coluna_ausente_no_layout_retorna_vazio() -> None:
    """Verifica validar codigo cargo coluna ausente no layout retorna vazio."""
    registros = [{"Nome": "Fulano"}]
    result = _validar_codigo_cargo(COLUNAS_SEM_CARGO, registros, {10, 20})
    assert result == {}


def test_validar_codigo_cargo_vazio_gera_erro() -> None:
    """Verifica validar codigo cargo vazio gera erro."""
    registros = [{"Codigo_do_Cargo": "", "Nome": "Fulano"}]
    erros = _validar_codigo_cargo(COLUNAS_COM_CARGO, registros, {10, 20})
    assert 2 in erros
    assert any("não pode estar em branco" in m for m in erros[2])


def test_validar_codigo_cargo_none_gera_erro() -> None:
    """Verifica validar codigo cargo none gera erro."""
    registros = [{"Codigo_do_Cargo": None, "Nome": "Fulano"}]
    erros = _validar_codigo_cargo(COLUNAS_COM_CARGO, registros, {10, 20})
    assert 2 in erros
    assert any("não pode estar em branco" in m for m in erros[2])


def test_validar_codigo_cargo_nao_inteiro_gera_erro() -> None:
    """Verifica validar codigo cargo nao inteiro gera erro."""
    registros = [{"Codigo_do_Cargo": "ABC", "Nome": "Fulano"}]
    erros = _validar_codigo_cargo(COLUNAS_COM_CARGO, registros, {10, 20})
    assert 2 in erros
    assert any("número inteiro válido" in m for m in erros[2])


def test_validar_codigo_cargo_decimal_gera_erro() -> None:
    """Verifica validar codigo cargo decimal gera erro."""
    registros = [{"Codigo_do_Cargo": "10.5", "Nome": "Fulano"}]
    erros = _validar_codigo_cargo(COLUNAS_COM_CARGO, registros, {10, 20})
    assert 2 in erros
    assert any("número inteiro válido" in m for m in erros[2])


def test_validar_codigo_cargo_nao_pertence_ao_concurso_gera_erro() -> None:
    """Verifica validar codigo cargo nao pertence ao concurso gera erro."""
    registros = [{"Codigo_do_Cargo": "99", "Nome": "Fulano"}]
    erros = _validar_codigo_cargo(COLUNAS_COM_CARGO, registros, {10, 20})
    assert 2 in erros
    assert any(
        "não possui relação com o concurso selecionado" in m for m in erros[2]
    )
    assert any("99" in m for m in erros[2])
    assert any("Códigos válidos: 10, 20" in m for m in erros[2])


def test_validar_codigo_cargo_valido_sem_erro() -> None:
    """Verifica validar codigo cargo valido sem erro."""
    registros = [{"Codigo_do_Cargo": "10", "Nome": "Fulano"}]
    erros = _validar_codigo_cargo(COLUNAS_COM_CARGO, registros, {10, 20})
    assert erros == {}


def test_validar_codigo_cargo_multiplas_linhas_erros_distintos() -> None:
    """Verifica validar codigo cargo multiplas linhas erros distintos."""
    registros = [
        {"Codigo_do_Cargo": "10", "Nome": "A"},
        {"Codigo_do_Cargo": "", "Nome": "B"},
        {"Codigo_do_Cargo": "XYZ", "Nome": "C"},
        {"Codigo_do_Cargo": "99", "Nome": "D"},
    ]
    erros = _validar_codigo_cargo(COLUNAS_COM_CARGO, registros, {10, 20})
    assert 2 not in erros
    assert 3 in erros and any(
        "não pode estar em branco" in m for m in erros[3]
    )
    assert 4 in erros and any("número inteiro válido" in m for m in erros[4])
    assert 5 in erros and any("não possui relação" in m for m in erros[5])


def test_validar_codigo_cargo_identificado_por_campo_payload() -> None:
    """Verifica validar codigo cargo identificado por campo payload."""
    colunas = {
        "email_col": None,
        "cpf_col": None,
        "dn_col": None,
        "cargo_col": "CodCargo",
        "obrigatorias": ["CodCargo"],
    }
    registros = [{"CodCargo": "99"}]
    erros = _validar_codigo_cargo(colunas, registros, {10, 20})
    assert 2 in erros
    assert any("não possui relação" in m for m in erros[2])


def _mock_concursos_service(codigos: set) -> Any:
    """Executa  mock concursos service."""
    mock_service = MagicMock()
    mock_service.obter_codigos_cargo_do_concurso.return_value = codigos
    return patch(
        "importa_arquivos.services.validacao_habilitados.ApiConcursosService",
        return_value=mock_service,
    )


class _FakeImportacaoObj:
    """Define _FakeImportacaoObj."""

    concurso_uuid = "uuid-concurso-123"
    status = "PENDENTE"

    def save(self, **kwargs: Any) -> None:
        """Executa save."""
        pass


@pytest.mark.django_db
def test_validar_csv_habilitados_codigo_cargo_valido(
    layout_com_cargo: Any,
) -> None:
    """Verifica validar csv habilitados codigo cargo valido."""
    csv_text = "Inscricao,Nome,CPF,Codigo_do_Cargo\n1,Fulano,39053344705,10\n"
    with _mock_concursos_service({10, 20}):
        registros, _ = validar_csv_habilitados(
            _csv_bytes(csv_text), importacao_obj=_FakeImportacaoObj()
        )
    assert len(registros) == 1


@pytest.mark.django_db
def test_validar_csv_habilitados_codigo_cargo_vazio_lanca_excecao(
    layout_com_cargo: Any,
) -> None:
    """Verifica validar csv habilitados codigo cargo vazio lanca excecao."""
    csv_text = "Inscricao,Nome,CPF,Codigo_do_Cargo\n1,Fulano,39053344705,\n"
    with _mock_concursos_service({10, 20}):
        with pytest.raises(ColunaCSVInvalidaException) as exc:
            validar_csv_habilitados(
                _csv_bytes(csv_text), importacao_obj=_FakeImportacaoObj()
            )
    assert "não pode estar em branco" in exc.value.detalhes


@pytest.mark.django_db
def test_validar_csv_habilitados_codigo_cargo_sem_relacao_lanca_excecao(
    layout_com_cargo: Any,
) -> None:
    """Verifica validar csv habilitados codigo cargo sem relacao lanca excecao."""
    csv_text = "Inscricao,Nome,CPF,Codigo_do_Cargo\n1,Fulano,39053344705,999\n"
    with _mock_concursos_service({10, 20}):
        with pytest.raises(ColunaCSVInvalidaException) as exc:
            validar_csv_habilitados(
                _csv_bytes(csv_text), importacao_obj=_FakeImportacaoObj()
            )
    assert (
        "não possui relação com o concurso selecionado" in exc.value.detalhes
    )
    assert "999" in exc.value.detalhes
    assert "Códigos válidos" in exc.value.detalhes


@pytest.mark.django_db
def test_validar_csv_habilitados_multiplos_cargos_validos(
    layout_com_cargo: Any,
) -> None:
    """Verifica validar csv habilitados multiplos cargos validos."""
    csv_text = "Inscricao,Nome,CPF,Codigo_do_Cargo\n1,Fulano,39053344705,10\n2,Ciclano,17888214088,20\n"  # noqa: E501
    with _mock_concursos_service({10, 20}):
        registros, _ = validar_csv_habilitados(
            _csv_bytes(csv_text), importacao_obj=_FakeImportacaoObj()
        )
    assert len(registros) == 2


@pytest.mark.django_db
def test_validar_csv_habilitados_api_concursos_indisponivel_lanca_excecao(
    layout_com_cargo: Any,
) -> None:
    """Verifica validar csv habilitados api concursos indisponivel lanca."""
    csv_text = "Inscricao,Nome,CPF,Codigo_do_Cargo\n1,Fulano,39053344705,10\n"
    mock_service = MagicMock()
    mock_service.obter_codigos_cargo_do_concurso.side_effect = (
        CargoConcursoInvalidoException(
            mensagem="Serviço de concursos indisponível.", detalhes="timeout"
        )
    )
    with (
        patch(
            "importa_arquivos.services.validacao_habilitados.ApiConcursosService",
            return_value=mock_service,
        ),
        pytest.raises(CargoConcursoInvalidoException),
    ):
        validar_csv_habilitados(
            _csv_bytes(csv_text), importacao_obj=_FakeImportacaoObj()
        )

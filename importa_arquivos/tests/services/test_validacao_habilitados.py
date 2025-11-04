import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from importa_arquivos.services.validacao_habilitados import validar_csv_habilitados
from importa_arquivos.services.exceptions import LayoutNaoConfiguradoException, ColunaCSVInvalidaException
from importa_arquivos.models import LayoutArquivoImportacao


pytestmark = pytest.mark.django_db


def test_validar_csv_habilitados_sucesso(layout_habilitados):
    csv = 'CPF\n17888214088\n'
    arquivo = SimpleUploadedFile('h.csv', csv.encode('utf-8-sig'), content_type='text/csv')

    registros, estrutura = validar_csv_habilitados(arquivo)
    assert len(registros) == 1
    assert registros[0]['CPF'] == '17888214088'
    assert isinstance(estrutura, list)


def test_validar_csv_habilitados_sem_layout():
    arquivo = SimpleUploadedFile('h.csv', b'CPF\n123\n', content_type='text/csv')
    with pytest.raises(LayoutNaoConfiguradoException):
        validar_csv_habilitados(arquivo)


def _criar_layout_minimo():
    estrutura = [
        {"coluna": "Inscricao", "campo_payload": "codigo_inscricao", "obrigatorio": 1},
        {"coluna": "Nome", "campo_payload": "nome", "obrigatorio": 1},
        {"coluna": "DataNascimento", "campo_payload": "data_nascimento", "obrigatorio": 0},
        {"coluna": "CPF", "campo_payload": "cpf", "obrigatorio": 1},
        {"coluna": "Email", "campo_payload": "email", "obrigatorio": 0},
    ]
    LayoutArquivoImportacao.objects.create(tipo='HABILITADOS', estrutura=estrutura)


def _csv_bytes(text: str) -> io.BytesIO:
    return io.BytesIO(text.encode('utf-8'))


def test_validacao_sucesso_minimo():
    _criar_layout_minimo()
    csv_text = (
        "Inscricao,Nome,DataNascimento,CPF,Email\n"
        "00000001,Fulano,05/29/1990,39053344705,fulano@example.com\n"
    )
    registros, _ = validar_csv_habilitados(_csv_bytes(csv_text))
    assert len(registros) == 1 and registros[0]['Nome'] == 'Fulano'


def test_obrigatorios_agrupados_mesma_linha():
    _criar_layout_minimo()
    csv_text = (
        "Inscricao,Nome,DataNascimento,CPF,Email\n"
        ",,05/29/1990,,valid@example.com\n"
    )
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert 'Linha 2' in exc.value.detalhes
    assert 'Campos obrigatórios vazios' in exc.value.detalhes
    assert 'Nome' in exc.value.detalhes and 'CPF' in exc.value.detalhes


def test_email_invalido_agregado():
    _criar_layout_minimo()
    csv_text = (
        "Inscricao,Nome,DataNascimento,CPF,Email\n"
        "1,Fulano,05/29/1990,39053344705,foo@bar\n"
    )
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert 'Linha 2' in exc.value.detalhes and 'Email inválido' in exc.value.detalhes


def test_cpf_invalido_agregado():
    _criar_layout_minimo()
    csv_text = (
        "Inscricao,Nome,DataNascimento,CPF,Email\n"
        "1,Fulano,05/29/1990,12345678900,fulano@example.com\n"
    )
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert 'Linha 2' in exc.value.detalhes and 'CPF inválido' in exc.value.detalhes


def test_data_nascimento_invalida_agregada():
    _criar_layout_minimo()
    csv_text = (
        "Inscricao,Nome,DataNascimento,CPF,Email\n"
        "1,Fulano,29/05/1990,39053344705,fulano@example.com\n"
    )
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    assert 'Linha 2' in exc.value.detalhes and 'dataNascimento inválida' in exc.value.detalhes


def test_erros_agregados_mesma_linha():
    _criar_layout_minimo()
    csv_text = (
        "Inscricao,Nome,DataNascimento,CPF,Email\n"
        "1,,05/29/1990,12345678900,foo@bar\n"
    )
    with pytest.raises(ColunaCSVInvalidaException) as exc:
        validar_csv_habilitados(_csv_bytes(csv_text))
    detalhes = exc.value.detalhes
    assert 'Linha 2' in detalhes
    assert 'Campos obrigatórios vazios' in detalhes and 'Nome' in detalhes
    assert 'Email inválido' in detalhes and 'CPF inválido' in detalhes

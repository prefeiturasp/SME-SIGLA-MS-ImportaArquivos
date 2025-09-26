import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from importa_arquivos.services.validacao_vagas import validar_csv_vagas
from importa_arquivos.services.exceptions import LayoutNaoConfiguradoException, LeituraCSVException, ColunaCSVInvalidaException


pytestmark = pytest.mark.django_db

def test_validar_csv_vagas_sucesso(layout_vagas):
    csv = 'DataFechamentoModulo\n05/09/2025\n'
    arquivo = SimpleUploadedFile('v.csv', csv.encode('utf-8'), content_type='text/csv')

    registros, estrutura = validar_csv_vagas(arquivo)
    assert len(registros) == 1
    assert registros[0]['DataFechamentoModulo'] == '05/09/2025'
    assert isinstance(estrutura, list)


def test_validar_csv_vagas_sem_layout():
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')
    with pytest.raises(LayoutNaoConfiguradoException):
        validar_csv_vagas(arquivo)


def test_validar_csv_vagas_erro_leitura_utf8(layout_vagas):
    conteudo_invalido = b"\xff\xfe\xfa\xfb"
    arquivo = SimpleUploadedFile('v.csv', conteudo_invalido, content_type='text/csv')

    with pytest.raises(LeituraCSVException) as excinfo:
        validar_csv_vagas(arquivo)

    assert str(excinfo.value) == 'Erro ao ler arquivo CSV'
    assert hasattr(excinfo.value, 'detalhes')


def test_validar_csv_vagas_colunas_invalidas(layout_vagas):
    # Cabeçalho não previsto pelo layout
    csv = 'OutroHeader\nvalor\n'
    arquivo = SimpleUploadedFile('v.csv', csv.encode('utf-8'), content_type='text/csv')

    with pytest.raises(ColunaCSVInvalidaException) as excinfo:
        validar_csv_vagas(arquivo)

    assert str(excinfo.value) == 'Colunas inválidas no arquivo CSV'
    assert hasattr(excinfo.value, 'detalhes')
    assert 'Encontradas:' in excinfo.value.detalhes
    assert 'Esperadas:' in excinfo.value.detalhes

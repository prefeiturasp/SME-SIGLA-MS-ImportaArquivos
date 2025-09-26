import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from importa_arquivos.services.validacao_habilitados import validar_csv_habilitados
from importa_arquivos.services.exceptions import LayoutNaoConfiguradoException


pytestmark = pytest.mark.django_db


def test_validar_csv_habilitados_sucesso(layout_habilitados):
    csv = 'CPF\n12345678900\n'
    arquivo = SimpleUploadedFile('h.csv', csv.encode('utf-8-sig'), content_type='text/csv')

    registros, estrutura = validar_csv_habilitados(arquivo)
    assert len(registros) == 1
    assert registros[0]['CPF'] == '12345678900'
    assert isinstance(estrutura, list)


def test_validar_csv_habilitados_sem_layout():
    arquivo = SimpleUploadedFile('h.csv', b'CPF\n123\n', content_type='text/csv')
    with pytest.raises(LayoutNaoConfiguradoException):
        validar_csv_habilitados(arquivo)

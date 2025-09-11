import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from importa_arquivos.models.layout import LayoutArquivoImportacao
from importa_arquivos.services.validacao_habilitados import validar_csv_habilitados


@pytest.mark.django_db
def test_validar_csv_habilitados_sucesso():
    LayoutArquivoImportacao.objects.create(
        tipo='HABILITADOS',
        estrutura=[
            {'coluna': 'Inscricao', 'campo_payload': 'codigo_inscricao'},
            {'coluna': 'Nome', 'campo_payload': 'nome'},
        ],
    )

    csv = 'Inscricao,Nome\n123,Joao\n'
    arquivo = SimpleUploadedFile('h.csv', csv.encode('utf-8'), content_type='text/csv')

    registros, estrutura = validar_csv_habilitados(arquivo)
    assert len(registros) == 1
    assert registros[0]['Inscricao'] == '123'
    assert registros[0]['Nome'] == 'Joao'
    assert isinstance(estrutura, list)


@pytest.mark.django_db
def test_validar_csv_habilitados_sem_layout():
    arquivo = SimpleUploadedFile('h.csv', b'Inscricao,Nome\n1,A\n', content_type='text/csv')
    with pytest.raises(ValueError):
        validar_csv_habilitados(arquivo)

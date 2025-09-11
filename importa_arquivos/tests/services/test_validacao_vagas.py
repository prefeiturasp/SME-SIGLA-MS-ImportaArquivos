import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from importa_arquivos.models.layout import LayoutArquivoImportacao
from importa_arquivos.services.validacao_vagas import validar_csv_vagas


@pytest.mark.django_db
def test_validar_csv_vagas_sucesso():
    LayoutArquivoImportacao.objects.create(
        tipo='VAGAS',
        estrutura=[
            {'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'},
        ],
    )

    csv = 'DataFechamentoModulo\n05/09/2025\n'
    arquivo = SimpleUploadedFile('v.csv', csv.encode('utf-8'), content_type='text/csv')

    registros, estrutura = validar_csv_vagas(arquivo)
    assert len(registros) == 1
    assert registros[0]['DataFechamentoModulo'] == '05/09/2025'
    assert isinstance(estrutura, list)


@pytest.mark.django_db
def test_validar_csv_vagas_sem_layout():
    arquivo = SimpleUploadedFile('v.csv', b'DataFechamentoModulo\n05/09/2025\n', content_type='text/csv')
    with pytest.raises(ValueError):
        validar_csv_vagas(arquivo)

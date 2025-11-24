import pytest

from importa_arquivos.models import LayoutArquivoImportacao


pytestmark = pytest.mark.django_db

@pytest.fixture
def layout_vagas():
    return LayoutArquivoImportacao.objects.create(
        tipo='VAGAS',
        estrutura=[{'coluna': 'DataFechamentoModulo', 'campo_payload': 'data_fechamento_modulo'}],
    )


@pytest.fixture
def layout_habilitados():
    return LayoutArquivoImportacao.objects.create(
        tipo='HABILITADOS',
        estrutura=[{'coluna': 'CPF', 'campo_payload': 'cpf'}],
    )

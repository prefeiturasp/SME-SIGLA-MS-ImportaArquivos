import pytest
from unittest.mock import Mock

from importa_arquivos.models import ImportacaoArquivoVagas, ImportacaoErro
from importa_arquivos.services.erros import registrar_erro, captura_erros_importacao
from importa_arquivos.services.exceptions import BaseImportacaoException


pytestmark = pytest.mark.django_db


def test_registrar_erro_cria_registro_e_atualiza_status():
    obj = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='x.csv', arquivo='importacoes/x.csv', tipo='VAGAS'
    )

    registrar_erro(obj, mensagem='Falha', detalhes='detalhe')

    obj.refresh_from_db()
    assert obj.status == 'ERRO'
    assert ImportacaoErro.objects.filter(object_id=obj.uuid).count() == 1


def test_captura_erros_importacao_decorador_cria_registro():
    obj = ImportacaoArquivoVagas.objects.create(
        nome_arquivo='y.csv', arquivo='importacoes/y.csv', tipo='VAGAS'
    )

    @captura_erros_importacao('importacao_obj')
    def func_que_falha(importacao_obj=None):
        raise BaseImportacaoException('msg curta', detalhes='grande')

    with pytest.raises(BaseImportacaoException):
        func_que_falha(importacao_obj=obj)

    assert ImportacaoErro.objects.filter(object_id=obj.uuid).exists()

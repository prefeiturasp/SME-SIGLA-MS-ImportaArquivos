"""Testes unitários para os serializers de importação de escolhas."""
from __future__ import annotations
from typing import Any
import uuid
import pytest
from django.contrib.contenttypes.models import ContentType
from importa_arquivos.models import ImportacaoErro, ImportacaoEscolhas
from importa_arquivos.serializers.importacao_escolhas import EscolhaItemSerializer, EscolhasImportacaoSerializer, ImportacaoEscolhasCreateSerializer, ImportacaoEscolhasListSerializer, ResponseSerializer
pytestmark = pytest.mark.django_db

class TestImportacaoEscolhasCreateSerializer:
    """Testes para ImportacaoEscolhasCreateSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Testa serializer válido com todos os campos obrigatórios.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        processo_id = 123
        concurso_uuid = uuid.uuid4()
        data = {'processo_uuid': str(processo_uuid), 'processo_id': processo_id, 'concurso_uuid': str(concurso_uuid)}
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['processo_uuid'] == processo_uuid
        assert serializer.validated_data['processo_id'] == processo_id
        assert serializer.validated_data['concurso_uuid'] == concurso_uuid

    def test_serializer_invalido_sem_processo_uuid(self) -> None:
        """Testa que processo_uuid é obrigatório.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'processo_id': 123}
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'processo_uuid' in serializer.errors

    def test_serializer_valido_sem_processo_id(self) -> None:
        """Testa que processo_id é opcional (pode ser None).
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        data = {'processo_uuid': str(processo_uuid), 'concurso_uuid': str(concurso_uuid)}
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['processo_uuid'] == processo_uuid
        assert serializer.validated_data['concurso_uuid'] == concurso_uuid
        assert serializer.validated_data.get('processo_id') is None

    def test_serializer_invalido_processo_uuid_invalido(self) -> None:
        """Testa que processo_uuid deve ser um UUID válido.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'processo_uuid': 'invalid-uuid', 'processo_id': 123}
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'processo_uuid' in serializer.errors

    def test_serializer_invalido_processo_id_nao_inteiro(self) -> None:
        """Testa que processo_id deve ser um inteiro.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        data = {'processo_uuid': str(processo_uuid), 'processo_id': 'not-an-integer'}
        serializer = ImportacaoEscolhasCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'processo_id' in serializer.errors

class TestImportacaoEscolhasListSerializer:
    """Testes para ImportacaoEscolhasListSerializer."""

    def test_serializer_lista_todos_campos(self) -> None:
        """Testa que o serializer lista todos os campos esperados.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(processo_uuid=processo_uuid, processo_id=123, concurso_uuid=concurso_uuid, status='CONCLUIDO')
        serializer = ImportacaoEscolhasListSerializer(importacao)
        data = serializer.data
        assert 'uuid' in data
        assert 'processo_uuid' in data
        assert 'processo_id' in data
        assert 'concurso_uuid' in data
        assert 'dados_prodam' in data
        assert 'status' in data
        assert 'criado_em' in data
        assert 'atualizado_em' in data
        assert 'erros' in data

    def test_serializer_retorna_erros_vazios_quando_nao_existem(self) -> None:
        """Testa que erros retorna None quando não há erros.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(processo_uuid=processo_uuid, processo_id=123)
        serializer = ImportacaoEscolhasListSerializer(importacao)
        assert serializer.data['erros'] is None

    def test_serializer_retorna_erros_quando_existem(self) -> None:
        """Testa que erros são retornados quando existem.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(processo_uuid=processo_uuid, processo_id=123)
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(content_type=content_type, object_id=importacao.uuid, mensagem='Erro de teste', erros='Detalhes do erro')
        serializer = ImportacaoEscolhasListSerializer(importacao)
        erros = serializer.data['erros']
        assert erros is not None
        assert len(erros) == 1
        assert erros[0]['mensagem'] == 'Erro de teste'
        assert erros[0]['erros'] == 'Detalhes do erro'
        assert 'criado_em' in erros[0]

    def test_serializer_retorna_multiplos_erros_ordenados(self) -> None:
        """Testa que múltiplos erros são retornados ordenados por criado_em.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        importacao = ImportacaoEscolhas.objects.create(processo_uuid=processo_uuid, processo_id=123)
        content_type = ContentType.objects.get_for_model(ImportacaoEscolhas)
        ImportacaoErro.objects.create(content_type=content_type, object_id=importacao.uuid, mensagem='Erro 1', erros='Detalhes 1')
        import time
        time.sleep(0.01)
        ImportacaoErro.objects.create(content_type=content_type, object_id=importacao.uuid, mensagem='Erro 2', erros='Detalhes 2')
        serializer = ImportacaoEscolhasListSerializer(importacao)
        erros = serializer.data['erros']
        assert len(erros) == 2
        assert erros[0]['mensagem'] == 'Erro 2'
        assert erros[1]['mensagem'] == 'Erro 1'

class TestResponseSerializer:
    """Testes para ResponseSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Testa serializer válido com todos os campos obrigatórios.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'retorno': 'TRUE', 'mensagem': 'Sucesso', 'lstDadosResultadoConvocacaoIngresso': [{'codigoPessoaFisica': '12345678901', 'codigoCargo': '123', 'descricaoStatus': 'ALOCADO'}]}
        serializer = ResponseSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['retorno'] == 'TRUE'
        assert len(serializer.validated_data['lstDadosResultadoConvocacaoIngresso']) == 1

    def test_serializer_valido_com_lista_vazia(self) -> None:
        """Testa serializer válido com lista vazia.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'retorno': 'TRUE', 'mensagem': 'Sucesso', 'lstDadosResultadoConvocacaoIngresso': []}
        serializer = ResponseSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_invalido_sem_retorno(self) -> None:
        """Testa que retorno é obrigatório.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'mensagem': 'Sucesso', 'lstDadosResultadoConvocacaoIngresso': []}
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert 'retorno' in serializer.errors

    def test_serializer_invalido_sem_mensagem(self) -> None:
        """Testa que mensagem é obrigatória.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'retorno': 'TRUE', 'lstDadosResultadoConvocacaoIngresso': []}
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert 'mensagem' in serializer.errors

    def test_serializer_invalido_sem_lista_dados(self) -> None:
        """Testa que lstDadosResultadoConvocacaoIngresso é obrigatória.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'retorno': 'TRUE', 'mensagem': 'Sucesso'}
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert 'lstDadosResultadoConvocacaoIngresso' in serializer.errors

    def test_serializer_valida_campos_obrigatorios_em_cada_item(self) -> None:
        """Testa validação dos campos obrigatórios em cada item da lista.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'retorno': 'TRUE', 'mensagem': 'Sucesso', 'lstDadosResultadoConvocacaoIngresso': [{'codigoPessoaFisica': '12345678901', 'codigoCargo': '123', 'descricaoStatus': 'ALOCADO'}, {'codigoPessoaFisica': '98765432109'}]}
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert 'lstDadosResultadoConvocacaoIngresso' in serializer.errors

    def test_serializer_valida_que_cada_item_eh_dicionario(self) -> None:
        """Testa que cada item da lista deve ser um dicionário.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'retorno': 'TRUE', 'mensagem': 'Sucesso', 'lstDadosResultadoConvocacaoIngresso': ['not-a-dict']}
        serializer = ResponseSerializer(data=data)
        assert not serializer.is_valid()
        assert 'lstDadosResultadoConvocacaoIngresso' in serializer.errors

class TestEscolhaItemSerializer:
    """Testes para EscolhaItemSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Testa serializer válido com todos os campos.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'codigoPessoaFisica': '12345678901', 'codigoCargo': '123', 'codigoUnidadeAlocacao': '456789', 'tipoVaga': 'PRECARIA', 'descricaoStatus': 'ALOCADO'}
        serializer = EscolhaItemSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_valido_com_campos_opcionais_nulos(self) -> None:
        """Testa serializer válido com campos opcionais como None.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'codigoPessoaFisica': '12345678901', 'codigoCargo': '123', 'codigoUnidadeAlocacao': None, 'tipoVaga': None, 'descricaoStatus': 'ALOCADO'}
        serializer = EscolhaItemSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_invalido_sem_codigo_pessoa_fisica(self) -> None:
        """Testa que codigoPessoaFisica é obrigatório.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'codigoCargo': '123', 'descricaoStatus': 'ALOCADO'}
        serializer = EscolhaItemSerializer(data=data)
        assert not serializer.is_valid()
        assert 'codigoPessoaFisica' in serializer.errors

class TestEscolhasImportacaoSerializer:
    """Testes para EscolhasImportacaoSerializer."""

    def test_serializer_valido_com_dados_completos(self) -> None:
        """Testa serializer válido com todos os campos obrigatórios.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        concurso_uuid = uuid.uuid4()
        data = {'processo_uuid': str(processo_uuid), 'concurso_uuid': str(concurso_uuid), 'escolhas': [{'cpf': '12345678901', 'codigo_cargo': '123', 'situacao': 'ESCOLHA'}]}
        serializer = EscolhasImportacaoSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_invalido_sem_processo_uuid(self) -> None:
        """Testa que processo_uuid é obrigatório.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        data = {'escolhas': [{'cpf': '12345678901', 'codigo_cargo': '123', 'situacao': 'ESCOLHA'}]}
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert 'processo_uuid' in serializer.errors

    def test_serializer_invalido_sem_escolhas(self) -> None:
        """Testa que escolhas é obrigatório.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        data = {'processo_uuid': str(processo_uuid)}
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert 'escolhas' in serializer.errors

    def test_serializer_valida_campos_obrigatorios_em_cada_escolha(self) -> None:
        """Testa validação dos campos obrigatórios em cada escolha.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        data = {'processo_uuid': str(processo_uuid), 'escolhas': [{'cpf': '12345678901', 'codigo_cargo': '123', 'situacao': 'ESCOLHA'}, {'cpf': '98765432109'}]}
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert 'escolhas' in serializer.errors

    def test_serializer_valida_cpf_obrigatorio(self) -> None:
        """Testa que cpf é obrigatório em cada escolha.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        processo_uuid = uuid.uuid4()
        data = {'processo_uuid': str(processo_uuid), 'escolhas': [{'codigo_cargo': '123', 'situacao': 'ESCOLHA'}]}
        serializer = EscolhasImportacaoSerializer(data=data)
        assert not serializer.is_valid()
        assert 'escolhas' in serializer.errors

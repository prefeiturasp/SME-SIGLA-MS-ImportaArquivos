"""Serviço de exportação de candidatos por processo.

Exige cargo_codigo (payload/registro). concurso_uuid e concurso_nome são
opcionais.
concurso_codigo e concurso_data_criacao são opcionais (preenchidos no model
quando informados).
Busca habilitados na API Candidatos, monta dados_concurso e lista_candidatos e
formata o arquivo .txt (pipe, DD/MM/YYYY, CPF só dígitos).
"""
from __future__ import annotations
import re
from typing import Any
from exporta_arquivo.models import ExportacaoCandidatosProcesso
from exporta_arquivo.services import ApiCandidatosService, ApiConcursosService
SEP = '|'
COLUNAS_LINHA = ['codigo', 'data_criacao', 'cd_cpf', 'nm_candidato_concurso', 'dt_nascimento', 'cd_sexo', 'nr_rg', 'cd_cep', 'nm_logradouro', 'nr_logradouro', 'tx_complemento', 'nm_bairro', 'nm_município', 'sg_unidade_federativa', 'nm_email', 'nr_telefone_fixo', 'nr_telefone_celular', 'cd_cargo', 'cd_vinculo', 'cd_registro_funcional', 'nr_classificação', 'nr_desempate', 'nr_classificação_concurso']

def _data_para_dd_mm_yyyy(val: Any) -> str:
    """Converte data (ISO ou string) para DD/MM/YYYY.
    
    Args:
        val: Parâmetro val da operação.
    
    Returns:
        Texto resultante da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    if val is None or val == '':
        return ''
    s = str(val).strip()
    if not s:
        return ''
    if 'T' in s:
        s = s.split('T')[0]
    if '-' in s:
        partes = s.split('-')
        if len(partes) == 3:
            return f'{partes[2]}/{partes[1]}/{partes[0]}'
    if '/' in s and len(s) >= 8:
        return s
    return s

def _cpf_apenas_digitos(val: Any) -> str:
    """Retorna CPF apenas com dígitos.
    
    Args:
        val: Parâmetro val da operação.
    
    Returns:
        Texto resultante da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return re.sub('\\D', '', str(val)) if val is not None else ''

def _campo(val: Any) -> str:
    """Normaliza valor para o arquivo (sem pipe no conteúdo).
    
    Args:
        val: Parâmetro val da operação.
    
    Returns:
        Texto resultante da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    if val is None:
        return ''
    s = str(val).strip().replace('\r', ' ').replace('\n', ' ')
    return s.replace(SEP, ' ') if SEP in s else s

def formatar_arquivo_candidatos_processo(linhas_candidatos: list[dict[str, Any]]) -> str:
    """Gera o conteúdo do arquivo TXT (delimitado por |) sem cabeçalho.
    
    Args:
        linhas_candidatos: Parâmetro linhas candidatos da operação.
    
    Returns:
        Texto resultante da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    linhas: list[str] = []
    for item in linhas_candidatos:
        if not isinstance(item, dict):
            continue
        valores: list[str] = []
        for col in COLUNAS_LINHA:
            valores.append(_campo(item.get(col)))
        linhas.append(SEP.join(valores))
    return '\n'.join(linhas) + '\n' if linhas else ''

def _mapear_habilitado_para_exportacao(item: dict[str, Any], dados_concurso: dict[str, Any]) -> dict[str, Any]:
    """Mapeia item da API de habilitados para a estrutura do arquivo (colunas.
    
    Args:
        item: Parâmetro item da operação.
        dados_concurso: Parâmetro dados concurso da operação.
    
    Returns:
        Dicionário com os dados processados.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    candidato = item.get('candidato') if isinstance(item.get('candidato'), dict) else {}
    dt_nasc = candidato.get('data_nascimento')  # type: ignore[union-attr]
    dt_nasc = (str(dt_nasc).split('T')[0] if dt_nasc else '') if dt_nasc is not None else ''
    return {'codigo': dados_concurso.get('codigo'), 'data_criacao': _data_para_dd_mm_yyyy(dados_concurso.get('criado_em')), 'cd_cpf': _cpf_apenas_digitos(candidato.get('cpf')) or '', 'nm_candidato_concurso': candidato.get('nome') or '', 'dt_nascimento': _data_para_dd_mm_yyyy(dt_nasc), 'cd_sexo': candidato.get('genero') or '', 'nr_rg': candidato.get('rg') or '', 'cd_cep': candidato.get('cep') or '', 'nm_logradouro': candidato.get('endereco') or '', 'nr_logradouro': candidato.get('numero') or '', 'tx_complemento': candidato.get('complemento') or '', 'nm_bairro': candidato.get('bairro') or '', 'nm_município': candidato.get('cidade') or '', 'sg_unidade_federativa': candidato.get('estado') or '', 'nm_email': candidato.get('email') or '', 'nr_telefone_fixo': candidato.get('telefone') or '', 'nr_telefone_celular': candidato.get('celular') or '', 'cd_cargo': item.get('codigo_cargo') or '', 'cd_vinculo': candidato.get('vinculo') or '', 'cd_registro_funcional': candidato.get('registro_funcional') or '', 'nr_classificação': item.get('ranking_escolha'), 'nr_desempate': '', 'nr_classificação_concurso': item.get('classificacao')}  # type: ignore[union-attr]

def exportar_candidatos_processo(instance: ExportacaoCandidatosProcesso) -> str:
    """Orquestra a exportação de candidatos por processo.
    
    Args:
        instance: Instância do modelo em atualização.
    
    Returns:
        Texto resultante da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    dados_concurso = ApiConcursosService().get_concurso(instance.concurso_uuid)  # type: ignore[arg-type]
    instance.concurso_codigo = dados_concurso.get('codigo')
    instance.concurso_data_criacao = dados_concurso.get('criado_em')
    instance.save(update_fields=['concurso_codigo', 'concurso_data_criacao'])
    lista_habilitados = ApiCandidatosService().get_habilitados(processo_uuid=instance.processo_uuid, codigo_cargo=instance.cargo_codigo, lote__concurso_uuid=instance.concurso_uuid)

    def _chave(i: Any) -> Any:
        """Executa  chave.
        
        Args:
            i: Parâmetro i da operação.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return (i.get('ranking_escolha') is None, i.get('ranking_escolha') or 0)
    lista_ordenada = sorted((i for i in lista_habilitados if isinstance(i, dict)), key=_chave)
    lista_candidatos = [_mapear_habilitado_para_exportacao(item, dados_concurso) for item in lista_ordenada]
    conteudo_formatado = formatar_arquivo_candidatos_processo(lista_candidatos)
    return conteudo_formatado

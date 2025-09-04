#!/usr/bin/env python3
"""
Script de teste para validar a integração completa do sistema.
Testa: layouts, criação de importações, comunicação com robust server.
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from importa_arquivos.models import ImportacaoArquivos
from importa_arquivos.layout_service import LayoutService


def testar_layouts():
    """Testa se os layouts foram carregados corretamente."""
    print("🧪 Testando layouts...")
    
    layouts = LayoutService.list_layouts()
    print(f"   📊 Total de layouts: {len(layouts)}")
    
    # Verificar layouts específicos
    layout_vagas = LayoutService.get_layout_by_tipo('VAGAS')
    layout_candidatos = LayoutService.get_layout_by_tipo('HABILITADOS')
    
    if layout_vagas:
        total_campos = len(layout_vagas.get('dados', []))
        print(f"   ✅ Layout VAGAS encontrado: {total_campos} campos")
    else:
        print("   ❌ Layout VAGAS não encontrado")
        return False
    
    if layout_candidatos:
        total_campos = len(layout_candidatos.get('dados', []))
        print(f"   ✅ Layout HABILITADOS encontrado: {total_campos} campos")
    else:
        print("   ❌ Layout HABILITADOS não encontrado")
        return False
    
    return True


def testar_api_layouts():
    """Testa a API de layouts."""
    print("\n🧪 Testando API de layouts...")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/layouts/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API respondeu com {len(data.get('results', []))} layouts")
            return True
        else:
            print(f"   ❌ API retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ⚠️  API não está disponível (servidor não está rodando)")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao testar API: {e}")
        return False


def testar_robust_server():
    """Testa se o robust server está funcionando."""
    print("\n🧪 Testando Robust Server...")
    
    try:
        response = requests.get('http://localhost:8003/api/health', timeout=5)
        if response.status_code == 200:
            print("   ✅ Robust Server está funcionando")
            return True
        else:
            print(f"   ❌ Robust Server retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ⚠️  Robust Server não está disponível")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao testar Robust Server: {e}")
        return False


def testar_criacao_importacao():
    """Testa a criação de uma importação via código."""
    print("\n🧪 Testando criação de importação...")
    
    try:
        # Contar importações antes
        count_antes = ImportacaoArquivos.objects.count()
        
        # Criar uma importação de teste
        importacao = ImportacaoArquivos.objects.create(
            concurso='Teste Sistema Completo',
            cargo='Cargo Teste',
            tipo_de_layout='VAGAS'
        )
        
        print(f"   ✅ Importação criada: {importacao.uuid}")
        
        # Verificar se foi criada
        count_depois = ImportacaoArquivos.objects.count()
        if count_depois == count_antes + 1:
            print("   ✅ Importação salva no banco")
            
            # Limpar teste
            importacao.delete()
            return True
        else:
            print("   ❌ Importação não foi salva corretamente")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao criar importação: {e}")
        return False


def criar_arquivo_teste():
    """Cria um arquivo CSV de teste."""
    arquivo_path = '/tmp/teste_sistema.csv'
    conteudo = """Inscricao,Nome,DataNascimento
12345,João da Silva,1990-01-15
67890,Maria Santos,1985-05-20"""
    
    with open(arquivo_path, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    return arquivo_path


def testar_api_completa():
    """Testa a API completa de importação."""
    print("\n🧪 Testando API completa de importação...")
    
    try:
        # Criar arquivo de teste
        arquivo_path = criar_arquivo_teste()
        
        # Dados para envio
        data = {
            'concurso': 'Teste API Completa',
            'cargo': 'Cargo API Teste',
            'tipo_de_layout': 'VAGAS'
        }
        
        # Arquivo para upload
        files = {
            'arquivo': open(arquivo_path, 'rb')
        }
        
        # Fazer requisição
        response = requests.post(
            'http://localhost:8000/api/v1/importacao-arquivos/',
            data=data,
            files=files,
            timeout=10
        )
        
        files['arquivo'].close()
        os.remove(arquivo_path)
        
        if response.status_code == 201:
            response_data = response.json()
            print(f"   ✅ Importação criada via API: {response_data.get('uuid')}")
            print(f"   📊 Status: {response_data.get('status')}")
            return True
        elif response.status_code == 503:
            print("   ⚠️  API retornou 503 (Robust Server indisponível) - comportamento esperado")
            return True
        else:
            print(f"   ❌ API retornou status {response.status_code}")
            print(f"   📄 Resposta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  API não está disponível")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao testar API: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("🚀 Iniciando testes do sistema completo...")
    print(f"🕐 Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    resultados = {
        'layouts': testar_layouts(),
        'api_layouts': testar_api_layouts(),
        'robust_server': testar_robust_server(),
        'criacao_importacao': testar_criacao_importacao(),
        'api_completa': testar_api_completa()
    }
    
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL:")
    
    total_testes = len(resultados)
    testes_passou = sum(resultados.values())
    
    for teste, resultado in resultados.items():
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"   {teste.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 RESULTADO: {testes_passou}/{total_testes} testes passaram")
    
    if testes_passou == total_testes:
        print("🎉 SISTEMA COMPLETO FUNCIONANDO!")
        return 0
    else:
        print("⚠️  ALGUNS COMPONENTES PRECISAM DE ATENÇÃO")
        return 1


if __name__ == '__main__':
    sys.exit(main())

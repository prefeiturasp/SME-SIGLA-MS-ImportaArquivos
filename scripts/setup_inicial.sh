#!/bin/bash
# Script de configuração inicial do sistema de importação de arquivos

echo "🚀 Configuração inicial do sistema..."
echo "=================================="

# Função para verificar se comando foi bem-sucedido
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1"
        exit 1
    fi
}

# 1. Aplicar migrações
echo "📊 Aplicando migrações do banco de dados..."
python manage.py migrate
check_success "Migrações aplicadas"

# 2. Carregar layouts iniciais
echo "📋 Carregando layouts iniciais..."
python manage.py carregar_layouts_iniciais --clean
check_success "Layouts iniciais carregados"

# 3. Verificar se existe superusuário
echo "👤 Verificando superusuário..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    print('Nenhum superusuário encontrado. Execute: python manage.py createsuperuser')
else:
    print('Superusuário já existe')
"

# 4. Coletar arquivos estáticos (se necessário)
echo "📁 Verificando arquivos estáticos..."
if [ -d "static" ]; then
    python manage.py collectstatic --noinput
    check_success "Arquivos estáticos coletados"
else
    echo "⏭️  Diretório static não existe - pulando"
fi

# 5. Executar testes do sistema
echo "🧪 Executando testes do sistema..."
python scripts/teste_sistema_completo.py
if [ $? -eq 0 ]; then
    echo "✅ Todos os testes passaram"
else
    echo "⚠️  Alguns testes falharam - verifique se os servidores estão rodando"
fi

echo ""
echo "🎉 Configuração inicial concluída!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Iniciar servidor Django: python manage.py runserver"
echo "   2. Iniciar Robust Server: python robust_server.py"
echo "   3. Acessar admin: http://localhost:8000/admin/"
echo "   4. Acessar API: http://localhost:8000/api/v1/"
echo ""
echo "🔧 Comandos úteis:"
echo "   - Recarregar layouts: python manage.py carregar_layouts_iniciais --force"
echo "   - Criar importações teste: python manage.py criar_importacoes --count 5"
echo "   - Limpar importações: python manage.py limpar_importacoes --confirm"
echo "   - Teste sistema: python scripts/teste_sistema_completo.py"

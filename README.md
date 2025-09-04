# SME-SIGLA-MS-ImportaArquivos

Sistema de importação de arquivos desenvolvido com Django REST Framework.

## 📁 Estrutura do Projeto

```
SME-SIGLA-MS-ImportaArquivos/
├── config/                          # Configurações do Django
│   ├── settings.py                  # Configurações principais
│   ├── urls.py                      # URLs principais
│   └── wsgi.py                      # Configuração WSGI
├── importa_arquivos/                # App principal
│   ├── models.py                    # Modelos de dados
│   ├── views.py                     # ViewSets da API
│   ├── serializers.py               # Serializers
│   ├── services.py                  # Serviços de importação
│   ├── admin.py                     # Configuração do admin
│   ├── utils.py                     # Utilitários
│   ├── tests/                       # Testes automatizados
│   │   ├── test_views.py            # Testes das views
│   │   └── conftest.py              # Configurações de teste
│   └── management/                  # Comandos customizados
│       └── commands/
│           ├── criar_importacoes.py
│           ├── limpar_importacoes.py
│           └── carregar_layouts_iniciais.py
├── data/                           # Dados iniciais do sistema
│   ├── layouts_iniciais.json       # Layouts padrão do sistema
│   └── README.md                   # Documentação dos dados iniciais
├── scripts/                        # Scripts utilitários
│   ├── setup_inicial.sh            # Script de configuração inicial
│   └── teste_sistema_completo.py   # Script de teste do sistema
├── requirements/                    # Dependências organizadas
│   ├── base.txt                     # Dependências principais
│   ├── local.txt                    # Desenvolvimento local
│   ├── production.txt               # Produção
│   └── README.md                    # Documentação dos requirements
├── docker-compose.yml              # Configuração Docker
├── env.example                     # Variáveis de ambiente (exemplo)
└── README_DOCKER.md               # Documentação Docker
```

## 🚀 Início Rápido

### 1. Configuração Inicial Automática

```bash
# Clonar o repositório
git clone <repository-url>
cd SME-SIGLA-MS-ImportaArquivos

# Copiar arquivo de ambiente (escolha uma opção)
cp env.example .env          # Para PostgreSQL
# ou
cp env.sqlite.example .env   # Para SQLite

# Executar configuração inicial completa
chmod +x scripts/setup_inicial.sh
./scripts/setup_inicial.sh
```

### 2. Configuração Manual (alternativa)

```bash

# Editar variáveis de ambiente
nano .env
```

### 2. Configurar banco de dados

#### Opção A: PostgreSQL (recomendado)

```bash
# Iniciar PostgreSQL com Docker
docker-compose up -d

# Verificar se está rodando
docker-compose ps
```

#### Opção B: SQLite (desenvolvimento rápido)

```bash
# Não precisa de Docker, apenas configure o .env
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=db.sqlite3
```

### 3. Instalar dependências

```bash
# Para desenvolvimento local
pip install -r requirements/local.txt

# Para produção
pip install -r requirements/production.txt

# Ou usar o arquivo padrão (desenvolvimento)
pip install -r requirements.txt

# Nota: Para SQLite, não precisa instalar psycopg2-binary
```

### 4. Configurar banco

```bash
# Executar migrações
python manage.py makemigrations
python manage.py migrate

# Criar superusuário (opcional)
python manage.py createsuperuser
```

### 5. Executar servidor

```bash
python manage.py runserver
```

## 🐳 Docker

### Iniciar serviços

```bash
# Iniciar PostgreSQL e pgAdmin
docker-compose up -d

# Verificar status
docker-compose ps
```

### Acessos

- **PostgreSQL**: localhost:5432
  - Database: `db_sigla`
  - Usuário: `postgres`
  - Senha: `postgres`

- **pgAdmin**: http://localhost:8080
  - Email: `admin@sigla.com`
  - Senha: `admin123`

## 📋 Sistema de Layouts Iniciais

O sistema inclui um mecanismo de carga inicial de layouts através de arquivos JSON:

### Layouts Disponíveis

- **VAGAS**: Layout simples com 3 campos (Inscricao, Nome, DataNascimento)
- **HABILITADOS**: Layout completo com 29 campos para candidatos habilitados

### Comando de Carga

```bash
# Primeira instalação (remove layouts existentes)
python manage.py carregar_layouts_iniciais --clean

# Atualizar layouts existentes
python manage.py carregar_layouts_iniciais --force

# Carregar de arquivo customizado
python manage.py carregar_layouts_iniciais --file meu_layouts.json
```

### Estrutura do Arquivo JSON

Os layouts são definidos em `data/layouts_iniciais.json` seguindo a estrutura:

```json
[
    {
        "uuid": "string",
        "tipo_de_layout": "VAGAS",
        "dados": [
            {
                "tipo": "string",
                "campo": "Inscricao",
                "ordem": 1,
                "tamanho": 20,
                "regras_de_validacao": "obrigatorio,unico"
            }
        ]
    }
]
```

📖 **Documentação completa**: Ver `data/README.md`

## 🧪 Scripts de Teste

### Teste Completo do Sistema

```bash
# Testar todos os componentes
python scripts/teste_sistema_completo.py

# Setup inicial completo
./scripts/setup_inicial.sh
```

O script de teste verifica:
- ✅ Layouts carregados corretamente
- ✅ API funcionando
- ✅ Robust Server disponível
- ✅ Criação de importações
- ✅ Integração completa

## 📊 API Endpoints

### Importação de Arquivos

```
GET    /api/v1/importacao-arquivos/                    # Listar importações
POST   /api/v1/importacao-arquivos/                    # Criar importação
GET    /api/v1/importacao-arquivos/{id}/               # Detalhes da importação
PUT    /api/v1/importacao-arquivos/{id}/               # Atualizar importação
PATCH  /api/v1/importacao-arquivos/{id}/               # Atualização parcial
DELETE /api/v1/importacao-arquivos/{id}/               # Remover importação
GET    /api/v1/importacao-arquivos/?formato=select     # Formato select (dropdown)
GET    /api/v1/importacao-arquivos/?status=pendente    # Filtrar por status
GET    /api/v1/importacao-arquivos/?search=nome        # Buscar por nome/descrição
```

## 🛠️ Comandos Customizados

### Criar dados de exemplo

```bash
# Criar 5 importações padrão
python manage.py criar_importacoes

# Criar 10 importações com status específico
python manage.py criar_importacoes --count 10 --status processando

# Limpar dados existentes e criar novos
python manage.py criar_importacoes --count 5 --clean
```

### Limpeza de dados

```bash
# Remover todas as importações (com confirmação)
python manage.py limpar_importacoes

# Remover sem confirmação interativa
python manage.py limpar_importacoes --confirm

# Remover apenas importações com status específico
python manage.py limpar_importacoes --status erro --confirm

# Remover registros e arquivos físicos
python manage.py limpar_importacoes --delete-files --confirm
```

## 📋 Modelos de Dados

### ImportacaoArquivos

- **UUID**: Identificador único
- **nome**: Nome do arquivo de importação
- **descricao**: Descrição da importação (opcional)
- **arquivo**: Arquivo físico para importação
- **status**: Status atual da importação
- **criado_em**: Data de criação
- **atualizado_em**: Data de atualização

### Status Disponíveis

- `pendente`: Aguardando processamento
- `processando`: Em processamento
- `concluido`: Processamento concluído
- `erro`: Erro durante o processamento

## 🔧 Configuração

### Variáveis de Ambiente

Copie `env.example` para `.env` e configure:

```env
# Django Settings
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings - PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=db_sigla
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Database Settings - SQLite (alternativa)
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=db.sqlite3

# External Services (opcionais)
# API_SERVICE_URL=http://localhost:8001
# NOTIFICATION_SERVICE_URL=http://localhost:8002
```

### Gerar Secret Key

```bash
# Usar Django para gerar secret key
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 📦 Dependências

### Desenvolvimento

```bash
pip install -r requirements/local.txt
```

Inclui:
- Django e DRF
- PostgreSQL driver
- Ferramentas de teste (pytest)
- Qualidade de código (black, flake8)
- Documentação (Sphinx)

### Produção

```bash
pip install -r requirements/production.txt
```

Inclui:
- Django e DRF
- Servidor WSGI (gunicorn)
- Arquivos estáticos (whitenoise)
- Segurança e monitoramento

## 🧪 Testes

```bash
# Executar testes
python manage.py test

# Com cobertura
pytest --cov=importa_arquivos
```

## 📚 Documentação

- [README Docker](README_DOCKER.md) - Configuração Docker
- [Requirements](requirements/README.md) - Estrutura de dependências

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para dúvidas ou problemas, abra uma issue no repositório. 
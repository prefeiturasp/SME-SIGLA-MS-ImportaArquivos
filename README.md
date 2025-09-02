# SME-SIGLA-MS-Concursos

Sistema de gerenciamento de concursos desenvolvido com Django REST Framework.

## 📁 Estrutura do Projeto

```
SME-SIGLA-MS-Concursos/
├── config/                          # Configurações do Django
│   ├── settings.py                  # Configurações principais
│   ├── urls.py                      # URLs principais
│   └── wsgi.py                      # Configuração WSGI
├── concursos/                       # App principal
│   ├── models.py                    # Modelos de dados
│   ├── views.py                     # ViewSets da API
│   ├── serializers.py               # Serializers
│   ├── services.py                  # Serviços externos
│   └── management/                  # Comandos customizados
│       └── commands/
│           ├── create_sample_concursos.py
│           ├── cleanup_concursos.py
│           ├── export_concursos.py
│           └── check_concursos.py
├── requirements/                    # Dependências organizadas
│   ├── base.txt                     # Dependências principais
│   ├── local.txt                    # Desenvolvimento local
│   ├── production.txt               # Produção
│   └── README.md                    # Documentação dos requirements
├── docker-compose.yml              # Configuração Docker
├── env.example                     # Variáveis de ambiente (exemplo)
├── generate_secret_key.py          # Script para gerar secret key
└── README_DOCKER.md               # Documentação Docker
```

## 🚀 Início Rápido

### 1. Configurar ambiente

```bash
# Clonar o repositório
git clone <repository-url>
cd SME-SIGLA-MS-Concursos

# Copiar arquivo de ambiente (escolha uma opção)
cp env.example .env          # Para PostgreSQL
# ou
cp env.sqlite.example .env   # Para SQLite

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
  - Database: `concursos`
  - Usuário: `postgres`
  - Senha: `postgres`

- **pgAdmin**: http://localhost:8080
  - Email: `admin@convocacao.com`
  - Senha: `admin123`

## 📊 API Endpoints

### Concursos

```
GET    /api/concursos/                    # Listar concursos
POST   /api/concursos/                    # Criar concurso
GET    /api/concursos/{id}/               # Detalhes do concurso
PUT    /api/concursos/{id}/               # Atualizar concurso
DELETE /api/concursos/{id}/               # Remover concurso
POST   /api/concursos/{id}/publish/       # Publicar concurso
POST   /api/concursos/{id}/cancel/        # Cancelar concurso
GET    /api/concursos/{id}/steps/         # Etapas do concurso
GET    /api/concursos/{id}/documents/     # Documentos do concurso
GET    /api/concursos/active/             # Concursos ativos
GET    /api/concursos/by_status/          # Filtrar por status
```

## 🛠️ Comandos Customizados

### Criar dados de exemplo

```bash
# Criar 5 concursos padrão
python manage.py create_sample_concursos

# Criar 10 concursos finalizados
python manage.py create_sample_concursos --count 10 --status FINALIZADO
```

### Verificar integridade

```bash
# Verificação básica
python manage.py check_concursos

# Verificação detalhada
python manage.py check_concursos --detailed
```

### Limpeza de dados

```bash
# Ver o que seria removido
python manage.py cleanup_concursos --dry-run

# Remover concursos antigos
python manage.py cleanup_concursos --days 30 --status CANCELADO
```

### Exportar dados

```bash
# Exportar todos os concursos
python manage.py export_concursos

# Exportar apenas concursos ativos
python manage.py export_concursos --status EM_ANDAMENTO --output ativos.json
```

## 📋 Modelos de Dados

### Concurso

- **UUID**: Identificador único
- **concurso_uuid**: UUID do concurso
- **concurso_nome**: Nome do concurso
- **descricao**: Tipo de descrição
- **tipo_concurso**: Tipo do concurso
- **status**: Status atual
- **data_publicacao**: Data de publicação
- **data_convocacao**: Data de convocação
- **numero_convocados**: Número de convocados
- **criado_em**: Data de criação
- **atualizado_em**: Data de atualização

### Status Disponíveis

- `EM_ANDAMENTO`: Em andamento
- `FINALIZADO`: Concluído
- `CANCELADO`: Cancelado

### Tipos de Concurso

- `CONVOCACAO`: Convocação
- `SELECAO`: Seleção
- `AVALIACAO`: Avaliação

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
DB_NAME=concursos
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Database Settings - SQLite (alternativa)
# DB_ENGINE=django.db.backends.sqlite3
# DB_NAME=db.sqlite3

# External Services
AUTH_SERVICE_URL=http://localhost:8001
NOTIFICATION_SERVICE_URL=http://localhost:8002
DOCUMENT_SERVICE_URL=http://localhost:8003
```

### Gerar Secret Key

```bash
# Usar o script incluído
python generate_secret_key.py

# Ou usar Django
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
pytest --cov=concursos
```

## 📚 Documentação

- [README Docker](README_DOCKER.md) - Configuração Docker
- [Requirements](requirements/README.md) - Estrutura de dependências
- [Comandos Customizados](concursos/management/README.md) - Comandos Django

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
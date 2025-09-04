# Sistema de Gerenciamento de Layouts

Este diretório contém os dados de configuração do sistema de importação de arquivos.

## Arquivo de Layouts

O arquivo `layouts.json` contém a definição dos layouts do sistema, armazenados em JSON ao invés do banco de dados:

- **VAGAS**: Layout simples com 3 campos (Inscricao, Nome, DataNascimento)
- **HABILITADOS**: Layout completo com 29 campos para candidatos habilitados

## Como Usar

### Comando de Gerenciamento

Use o comando Django de management para gerenciar os layouts:

```bash
# Carregar layouts de arquivo JSON
python manage.py gerenciar_layouts carregar --clean

# Listar layouts existentes
python manage.py gerenciar_layouts listar

# Criar backup dos layouts
python manage.py gerenciar_layouts backup

# Restaurar layouts de backup
python manage.py gerenciar_layouts restaurar backup_file.json

# Remover layout por UUID
python manage.py gerenciar_layouts remover <uuid>

# Exportar layouts para arquivo
python manage.py gerenciar_layouts exportar --output meus_layouts.json
```

### API REST

Os layouts também podem ser gerenciados via API REST:

```bash
# Listar layouts (retorna resumo sem campo 'dados')
GET /api/v1/layouts/

# Buscar layout por UUID (retorna dados completos incluindo 'dados')
GET /api/v1/layouts/{uuid}/

# Criar novo layout (aceita apenas 'tipo_de_layout' e 'dados')
POST /api/v1/layouts/
{
  "tipo_de_layout": "NOVO_LAYOUT",
  "dados": [
    {
      "tipo": "string",
      "campo": "Nome",
      "ordem": 1,
      "tamanho": 100,
      "regras_de_validacao": "obrigatorio"
    }
  ]
}

# Atualizar layout (aceita apenas 'tipo_de_layout' e 'dados')
PUT /api/v1/layouts/{uuid}/

# Remover layout
DELETE /api/v1/layouts/{uuid}/
```

#### Estrutura da API

**POST/PUT**: Aceita apenas os campos `tipo_de_layout` e `dados`. Campos como `uuid`, `total_campos` e `criado_em` são ignorados e gerados automaticamente.

**GET individual**: Retorna todos os campos incluindo o array `dados` completo com todos os subcampos.

**GET lista**: Retorna apenas campos de resumo (`uuid`, `tipo_de_layout`, `total_campos`, `criado_em`).

## Estrutura do Arquivo JSON

O arquivo deve conter uma lista de objetos JSON com a seguinte estrutura:

```json
[
    {
        "uuid": "string",                    // UUID único do layout
        "tipo_de_layout": "string",          // Tipo do layout (VAGAS, HABILITADOS, etc.)
        "dados": [                           // Array de campos do layout
            {
                "tipo": "string",            // Tipo do campo (string, integer, date, decimal, text)
                "campo": "string",           // Nome do campo
                "ordem": 1,                  // Ordem do campo no CSV
                "tamanho": 20,               // Tamanho máximo do campo
                "regras_de_validacao": "string" // Regras separadas por vírgula
            }
        ],
        "total_campos": 3,                   // Total de campos (calculado automaticamente)
        "criado_em": "2025-09-04T11:07:13.371479-03:00" // Timestamp (opcional)
    }
]
```

### Tipos de Campo Suportados

- `string`: Texto simples
- `integer`: Números inteiros
- `decimal`: Números decimais
- `date`: Datas
- `text`: Texto longo

### Regras de Validação Disponíveis

- `obrigatorio`: Campo obrigatório
- `opcional`: Campo opcional
- `unico`: Valor deve ser único
- `email_valido`: Validação de email
- `cpf_valido`: Validação de CPF
- `cep_valido`: Validação de CEP
- `uf_valida`: Validação de UF (estado)
- `data_valida`: Validação de data
- `ano_valido`: Validação de ano
- `maior_que_zero`: Valor deve ser maior que zero
- `maior_ou_igual_zero`: Valor deve ser maior ou igual a zero
- `opcoes:M,F`: Campo deve ser uma das opções especificadas

## Exemplo de Uso em Desenvolvimento

```bash
# Configuração inicial do ambiente
python manage.py migrate
python manage.py gerenciar_layouts carregar --clean

# Durante desenvolvimento, para resetar layouts
python manage.py gerenciar_layouts carregar --clean --force
```

## Logs e Feedback

O comando fornece feedback detalhado sobre o processo:

- ✅ Layouts criados com sucesso
- 🔄 Layouts atualizados
- ⏭️ Layouts ignorados (já existem)
- ❌ Layouts com erro de validação
- 📊 Estatísticas finais

## Validações Automáticas

O comando valida automaticamente:

- Formato JSON válido
- Campos obrigatórios presentes
- UUIDs válidos
- Estrutura dos dados de campos
- Regras de validação dos campos

## Integração com Deploy

Este comando pode ser integrado ao processo de deploy:

```bash
# No deploy
python manage.py migrate
python manage.py gerenciar_layouts carregar  # Não remove existentes
```

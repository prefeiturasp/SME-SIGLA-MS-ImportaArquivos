# Sistema de Carga Inicial de Layouts

Este diretório contém os dados iniciais para configuração do sistema de importação de arquivos.

## Arquivo de Layouts Iniciais

O arquivo `layouts_iniciais.json` contém a definição dos layouts padrão do sistema:

- **VAGAS**: Layout simples com 3 campos (Inscricao, Nome, DataNascimento)
- **CANDIDATOS_CLASSIFICADOS**: Layout completo com 29 campos para candidatos classificados

## Como Usar

### Comando de Carga Inicial

Use o comando Django de management para carregar os layouts:

```bash
# Carregar layouts pela primeira vez (limpa dados existentes)
python manage.py carregar_layouts_iniciais --clean

# Carregar layouts sem remover existentes
python manage.py carregar_layouts_iniciais

# Forçar atualização de layouts existentes
python manage.py carregar_layouts_iniciais --force

# Usar arquivo customizado
python manage.py carregar_layouts_iniciais --file meu_arquivo.json
```

### Opções Disponíveis

- `--clean`: Remove todos os layouts existentes antes de carregar os novos
- `--force`: Força a atualização de layouts existentes (baseado no UUID)
- `--file`: Especifica um arquivo JSON customizado (padrão: `data/layouts_iniciais.json`)

## Estrutura do Arquivo JSON

O arquivo deve conter uma lista de objetos JSON com a seguinte estrutura:

```json
[
    {
        "uuid": "string",                    // UUID único do layout
        "tipo_de_layout": "string",          // Tipo do layout (VAGAS, CANDIDATOS_CLASSIFICADOS, etc.)
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
python manage.py carregar_layouts_iniciais --clean

# Durante desenvolvimento, para resetar layouts
python manage.py carregar_layouts_iniciais --clean --force
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
python manage.py carregar_layouts_iniciais  # Não remove existentes
```

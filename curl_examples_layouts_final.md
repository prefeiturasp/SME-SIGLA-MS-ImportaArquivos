# Exemplos de cURL para API de Layouts - Funcionais

## Base URL
```
http://localhost:8000/api/v1/layouts/
```

## 1. Listar todos os layouts

### Listagem padrão
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json"
```

### Listagem formato select (para dropdowns)
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?formato=select" \
  -H "Content-Type: application/json"
```

### Filtrar por tipo de layout
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?tipo_de_layout=VAGAS" \
  -H "Content-Type: application/json"
```

```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?tipo_de_layout=CANDIDATOS_CLASSIFICADOS" \
  -H "Content-Type: application/json"
```

### Buscar por texto
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?search=VAGAS" \
  -H "Content-Type: application/json"
```

### Ordenação
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?ordering=tipo_de_layout" \
  -H "Content-Type: application/json"
```

```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?ordering=-criado_em" \
  -H "Content-Type: application/json"
```

### Paginação
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?page=1&page_size=10" \
  -H "Content-Type: application/json"
```

## 2. Criar um novo layout

### Layout para VAGAS
```bash
curl -X POST "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "VAGAS",
    "dados": [
      {
        "ordem": 1,
        "campo": "codigo_vaga",
        "tipo": "string",
        "tamanho": 10,
        "regras_de_validacao": "obrigatorio,unico"
      },
      {
        "ordem": 2,
        "campo": "titulo_vaga",
        "tipo": "string",
        "tamanho": 100,
        "regras_de_validacao": "obrigatorio"
      },
      {
        "ordem": 3,
        "campo": "descricao",
        "tipo": "text",
        "tamanho": 500,
        "regras_de_validacao": "opcional"
      },
      {
        "ordem": 4,
        "campo": "salario",
        "tipo": "decimal",
        "tamanho": 10,
        "regras_de_validacao": "numerico,maior_que_zero"
      },
      {
        "ordem": 5,
        "campo": "requisitos",
        "tipo": "text",
        "tamanho": 1000,
        "regras_de_validacao": "obrigatorio"
      }
    ]
  }'
```

### Layout para CANDIDATOS_CLASSIFICADOS
```bash
curl -X POST "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "CANDIDATOS_CLASSIFICADOS",
    "dados": [
      {
        "ordem": 1,
        "campo": "numero_inscricao",
        "tipo": "string",
        "tamanho": 15,
        "regras_de_validacao": "obrigatorio"
      },
      {
        "ordem": 2,
        "campo": "nome_candidato",
        "tipo": "string",
        "tamanho": 200,
        "regras_de_validacao": "obrigatorio"
      },
      {
        "ordem": 3,
        "campo": "cpf",
        "tipo": "string",
        "tamanho": 11,
        "regras_de_validacao": "obrigatorio,cpf_valido"
      },
      {
        "ordem": 4,
        "campo": "nota_objetiva",
        "tipo": "decimal",
        "tamanho": 5,
        "regras_de_validacao": "numerico,entre_0_e_100"
      },
      {
        "ordem": 5,
        "campo": "nota_redacao",
        "tipo": "decimal",
        "tamanho": 5,
        "regras_de_validacao": "numerico,entre_0_e_100"
      },
      {
        "ordem": 6,
        "campo": "nota_final",
        "tipo": "decimal",
        "tamanho": 5,
        "regras_de_validacao": "numerico,entre_0_e_100"
      },
      {
        "ordem": 7,
        "campo": "classificacao",
        "tipo": "integer",
        "tamanho": 5,
        "regras_de_validacao": "numerico,maior_que_zero"
      }
    ]
  }'
```

## 3. Buscar um layout específico

### Por UUID (substitua pelos UUIDs reais dos seus layouts)
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
  -H "Content-Type: application/json"
```

```bash
curl -X GET "http://localhost:8000/api/v1/layouts/f6574d20-ffa5-4d41-b610-bcde41efce62/" \
  -H "Content-Type: application/json"
```

## 4. Atualizar um layout

### Atualização completa (PUT)
```bash
curl -X PUT "http://localhost:8000/api/v1/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "VAGAS",
    "dados": [
      {
        "ordem": 1,
        "campo": "codigo_vaga",
        "tipo": "string",
        "tamanho": 12,
        "regras_de_validacao": "obrigatorio,unico"
      },
      {
        "ordem": 2,
        "campo": "titulo_vaga",
        "tipo": "string",
        "tamanho": 150,
        "regras_de_validacao": "obrigatorio"
      },
      {
        "ordem": 3,
        "campo": "salario_minimo",
        "tipo": "decimal",
        "tamanho": 10,
        "regras_de_validacao": "numerico,maior_que_zero"
      },
      {
        "ordem": 4,
        "campo": "salario_maximo",
        "tipo": "decimal",
        "tamanho": 10,
        "regras_de_validacao": "numerico,maior_que_zero"
      }
    ]
  }'
```

### Atualização parcial (PATCH)
```bash
curl -X PATCH "http://localhost:8000/api/v1/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
  -H "Content-Type: application/json" \
  -d '{
    "dados": [
      {
        "ordem": 1,
        "campo": "codigo_vaga_atualizado",
        "tipo": "string",
        "tamanho": 15,
        "regras_de_validacao": "obrigatorio,unico"
      },
      {
        "ordem": 2,
        "campo": "titulo_vaga",
        "tipo": "string",
        "tamanho": 100,
        "regras_de_validacao": "obrigatorio"
      }
    ]
  }'
```

## 5. Deletar um layout

```bash
curl -X DELETE "http://localhost:8000/api/v1/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
  -H "Content-Type: application/json"
```

## 6. Actions customizadas

### Buscar campos ordenados de um layout
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/campos_ordenados/" \
  -H "Content-Type: application/json"
```

### Listar tipos de layout disponíveis
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/tipos_disponiveis/" \
  -H "Content-Type: application/json"
```

## 7. Combinações de filtros e parâmetros

### Buscar layouts VAGAS ordenados por data de criação
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?tipo_de_layout=VAGAS&ordering=-criado_em" \
  -H "Content-Type: application/json"
```

### Buscar com paginação e filtro
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?tipo_de_layout=CANDIDATOS_CLASSIFICADOS&page=1&page_size=5" \
  -H "Content-Type: application/json"
```

### Buscar em formato select com filtro
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?formato=select&tipo_de_layout=VAGAS" \
  -H "Content-Type: application/json"
```

## 8. Exemplos de teste com dados reais

### Testar listagem (funcionando)
```bash
curl -s -X GET "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" | python -m json.tool
```

### Testar criação de layout simples
```bash
curl -X POST "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "VAGAS",
    "dados": [
      {
        "ordem": 1,
        "campo": "nome",
        "tipo": "string",
        "tamanho": 50,
        "regras_de_validacao": "obrigatorio"
      }
    ]
  }'
```

### Testar action personalizada - tipos disponíveis
```bash
curl -s -X GET "http://localhost:8000/api/v1/layouts/tipos_disponiveis/" \
  -H "Content-Type: application/json" | python -m json.tool
```

## 9. Exemplos de respostas esperadas

### Resposta da listagem padrão:
```json
{
  "links": {
    "next": null,
    "previous": null
  },
  "count": 2,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "uuid": "f6574d20-ffa5-4d41-b610-bcde41efce62",
      "tipo_de_layout": "CANDIDATOS_CLASSIFICADOS",
      "dados": [
        {
          "ordem": 1,
          "campo": "numero_inscricao",
          "tipo": "string",
          "tamanho": 15,
          "regras_de_validacao": "obrigatorio"
        },
        {
          "ordem": 2,
          "campo": "nome_candidato",
          "tipo": "string",
          "tamanho": 200,
          "regras_de_validacao": "obrigatorio"
        },
        {
          "ordem": 3,
          "campo": "nota_final",
          "tipo": "decimal",
          "tamanho": 5,
          "regras_de_validacao": "numerico,entre_0_e_100"
        },
        {
          "ordem": 4,
          "campo": "classificacao",
          "tipo": "integer",
          "tamanho": 5,
          "regras_de_validacao": "numerico,maior_que_zero"
        }
      ],
      "total_campos": 4,
      "criado_em": "2025-09-04T13:06:06.803302Z"
    },
    {
      "uuid": "30adb058-c79e-4bce-abcf-0d716edddeb9",
      "tipo_de_layout": "VAGAS",
      "dados": [
        {
          "ordem": 1,
          "campo": "codigo_vaga",
          "tipo": "string",
          "tamanho": 10,
          "regras_de_validacao": "obrigatorio,unico"
        },
        {
          "ordem": 2,
          "campo": "titulo_vaga",
          "tipo": "string",
          "tamanho": 100,
          "regras_de_validacao": "obrigatorio"
        },
        {
          "ordem": 3,
          "campo": "salario",
          "tipo": "decimal",
          "tamanho": 10,
          "regras_de_validacao": "numerico,maior_que_zero"
        }
      ],
      "total_campos": 3,
      "criado_em": "2025-09-04T13:06:06.789488Z"
    }
  ]
}
```

### Resposta do formato select:
```json
[
  {
    "value": "f6574d20-ffa5-4d41-b610-bcde41efce62",
    "label": "Layout CANDIDATOS_CLASSIFICADOS (4 campos)",
    "tipo_de_layout": "CANDIDATOS_CLASSIFICADOS"
  },
  {
    "value": "30adb058-c79e-4bce-abcf-0d716edddeb9",
    "label": "Layout VAGAS (3 campos)",
    "tipo_de_layout": "VAGAS"
  }
]
```

### Resposta dos tipos disponíveis:
```json
[
  {
    "value": "VAGAS",
    "label": "Vagas"
  },
  {
    "value": "CANDIDATOS_CLASSIFICADOS",
    "label": "Candidatos Classificados"
  }
]
```

### Resposta de um layout completo:
```json
{
  "uuid": "30adb058-c79e-4bce-abcf-0d716edddeb9",
  "tipo_de_layout": "VAGAS",
  "dados": [
    {
      "ordem": 1,
      "campo": "codigo_vaga",
      "tipo": "string",
      "tamanho": 10,
      "regras_de_validacao": "obrigatorio,unico"
    },
    {
      "ordem": 2,
      "campo": "titulo_vaga",
      "tipo": "string",
      "tamanho": 100,
      "regras_de_validacao": "obrigatorio"
    },
    {
      "ordem": 3,
      "campo": "salario",
      "tipo": "decimal",
      "tamanho": 10,
      "regras_de_validacao": "numerico,maior_que_zero"
    }
  ],
  "total_campos": 3,
  "criado_em": "2025-09-04T13:06:06.789488Z",
  "atualizado_em": "2025-09-04T13:06:06.789501Z"
}
```

### Resposta dos campos ordenados:
```json
{
  "uuid": "30adb058-c79e-4bce-abcf-0d716edddeb9",
  "tipo_de_layout": "VAGAS",
  "total_campos": 3,
  "campos": [
    {
      "ordem": 1,
      "campo": "codigo_vaga",
      "tipo": "string",
      "tamanho": 10,
      "regras_de_validacao": "obrigatorio,unico"
    },
    {
      "ordem": 2,
      "campo": "titulo_vaga",
      "tipo": "string",
      "tamanho": 100,
      "regras_de_validacao": "obrigatorio"
    },
    {
      "ordem": 3,
      "campo": "salario",
      "tipo": "decimal",
      "tamanho": 10,
      "regras_de_validacao": "numerico,maior_que_zero"
    }
  ]
}
```

## 10. Tratamento de erros

### Erro de validação - tipo inválido (400 Bad Request):
```bash
curl -X POST "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "TIPO_INVALIDO",
    "dados": []
  }'
```

### Erro de validação - dados inválidos (400 Bad Request):
```bash
curl -X POST "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "VAGAS",
    "dados": [
      {
        "ordem": "não é número",
        "campo": "teste",
        "tipo": "string",
        "tamanho": 10,
        "regras_de_validacao": "obrigatorio"
      }
    ]
  }'
```

### Erro de layout não encontrado (404 Not Found):
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/uuid-inexistente/" \
  -H "Content-Type: application/json"
```

## 11. Comandos para debug e teste

### Verificar se o servidor está rodando
```bash
curl -X GET "http://localhost:8000/api/v1/" \
  -H "Content-Type: application/json"
```

### Listar todos os layouts com saída formatada
```bash
curl -s -X GET "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" | python -m json.tool
```

### Contar total de layouts
```bash
curl -s -X GET "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" | python -c "import sys, json; data=json.load(sys.stdin); print(f'Total de layouts: {data[\"count\"]}')"
```

---

## Notas importantes:

1. **Base URL funcionando**: `http://localhost:8000/api/v1/layouts/`
2. **UUIDs reais do sistema**: 
   - VAGAS: `30adb058-c79e-4bce-abcf-0d716edddeb9`
   - CANDIDATOS_CLASSIFICADOS: `f6574d20-ffa5-4d41-b610-bcde41efce62`
3. **Validação rigorosa**: Todos os campos em `dados` são obrigatórios e tipados
4. **Estrutura obrigatória por item**: `ordem` (int), `campo` (string), `tipo` (string), `tamanho` (int), `regras_de_validacao` (string)
5. **Tipos aceitos**: Apenas `VAGAS` e `CANDIDATOS_CLASSIFICADOS`
6. **Paginação padrão**: 10 itens por página
7. **Actions customizadas funcionais**: `campos_ordenados` e `tipos_disponiveis`
8. **Filtros disponíveis**: `tipo_de_layout`, `search`, `ordering`, `formato=select`

Todos estes cURLs foram testados e estão funcionando no seu ambiente atual!

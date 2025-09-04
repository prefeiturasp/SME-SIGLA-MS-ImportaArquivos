# Exemplos de cURL para API de Layouts

## Base URL
```
http://localhost:8000/api/v1/importacao-arquivos/layouts/
```

## 1. Listar todos os layouts

### Listagem padrão
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/" \
  -H "Content-Type: application/json"
```

### Listagem formato select (para dropdowns)
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?formato=select" \
  -H "Content-Type: application/json"
```

### Filtrar por tipo de layout
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?tipo_de_layout=VAGAS" \
  -H "Content-Type: application/json"
```

```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?tipo_de_layout=CANDIDATOS_CLASSIFICADOS" \
  -H "Content-Type: application/json"
```

### Buscar por texto
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?search=VAGAS" \
  -H "Content-Type: application/json"
```

### Ordenação
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?ordering=tipo_de_layout" \
  -H "Content-Type: application/json"
```

```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?ordering=-criado_em" \
  -H "Content-Type: application/json"
```

### Paginação
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?page=1&page_size=10" \
  -H "Content-Type: application/json"
```

## 2. Criar um novo layout

### Layout para VAGAS
```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/layouts/" \
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
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/layouts/" \
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

### Por UUID (substitua pelo UUID real)
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
  -H "Content-Type: application/json"
```

## 4. Atualizar um layout

### Atualização completa (PUT)
```bash
curl -X PUT "http://localhost:8000/api/v1/importacao-arquivos/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
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
curl -X PATCH "http://localhost:8000/api/v1/importacao-arquivos/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
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
curl -X DELETE "http://localhost:8000/api/v1/importacao-arquivos/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/" \
  -H "Content-Type: application/json"
```

## 6. Actions customizadas

### Buscar campos ordenados de um layout
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/30adb058-c79e-4bce-abcf-0d716edddeb9/campos_ordenados/" \
  -H "Content-Type: application/json"
```

### Listar tipos de layout disponíveis
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/tipos_disponiveis/" \
  -H "Content-Type: application/json"
```

## 7. Combinações de filtros e parâmetros

### Buscar layouts VAGAS ordenados por data de criação
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?tipo_de_layout=VAGAS&ordering=-criado_em" \
  -H "Content-Type: application/json"
```

### Buscar com paginação e filtro
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?tipo_de_layout=CANDIDATOS_CLASSIFICADOS&page=1&page_size=5" \
  -H "Content-Type: application/json"
```

### Buscar em formato select com filtro
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/?formato=select&tipo_de_layout=VAGAS" \
  -H "Content-Type: application/json"
```

## 8. Exemplos de respostas esperadas

### Resposta da listagem padrão:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "uuid": "f6574d20-ffa5-4d41-b610-bcde41efce62",
      "tipo_de_layout": "CANDIDATOS_CLASSIFICADOS",
      "total_campos": 4,
      "criado_em": "2024-01-15T10:30:00Z"
    },
    {
      "uuid": "30adb058-c79e-4bce-abcf-0d716edddeb9",
      "tipo_de_layout": "VAGAS",
      "total_campos": 3,
      "criado_em": "2024-01-15T10:25:00Z"
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

## 9. Tratamento de erros

### Erro de validação (400 Bad Request):
```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "TIPO_INVALIDO",
    "dados": []
  }'
```

### Erro de layout não encontrado (404 Not Found):
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/layouts/uuid-inexistente/" \
  -H "Content-Type: application/json"
```

---

## Notas importantes:

1. **Base URL**: Ajuste `http://localhost:8000` para o seu ambiente
2. **UUIDs**: Substitua pelos UUIDs reais retornados pela API
3. **Validação**: Os dados JSON são validados conforme as regras definidas no modelo
4. **Estrutura obrigatória**: Cada item em `dados` deve conter: `ordem`, `campo`, `tipo`, `tamanho`, `regras_de_validacao`
5. **Tipos de layout**: Apenas `VAGAS` e `CANDIDATOS_CLASSIFICADOS` são aceitos
6. **Paginação**: Padrão de 20 itens por página, customize com `page_size`

# Exemplos da API de Layouts

Este documento demonstra como usar a API de layouts com a nova estrutura simplificada.

## 🔥 **POST - Criar Layout**

### Payload (apenas 2 campos necessários):
```json
{
  "tipo_de_layout": "HABILITADOS",
  "dados": [
    {
      "tipo": "string",
      "campo": "Matricula",
      "ordem": 1,
      "tamanho": 20,
      "regras_de_validacao": "obrigatorio,unico"
    },
    {
      "tipo": "string",
      "campo": "Nome",
      "ordem": 2,
      "tamanho": 200,
      "regras_de_validacao": "obrigatorio"
    },
    {
      "tipo": "string",
      "campo": "Email",
      "ordem": 3,
      "tamanho": 150,
      "regras_de_validacao": "obrigatorio,email_valido"
    }
  ]
}
```

### Resposta (todos os campos gerados automaticamente):
```json
{
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tipo_de_layout": "HABILITADOS",
  "dados": [
    {
      "tipo": "string",
      "campo": "Matricula",
      "ordem": 1,
      "tamanho": 20,
      "regras_de_validacao": "obrigatorio,unico"
    },
    {
      "tipo": "string",
      "campo": "Nome",
      "ordem": 2,
      "tamanho": 200,
      "regras_de_validacao": "obrigatorio"
    },
    {
      "tipo": "string",
      "campo": "Email",
      "ordem": 3,
      "tamanho": 150,
      "regras_de_validacao": "obrigatorio,email_valido"
    }
  ],
  "total_campos": 3,
  "criado_em": "2025-09-08T13:30:00.000000+00:00"
}
```

### cURL:
```bash
curl -X POST "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "HABILITADOS",
    "dados": [
      {
        "tipo": "string",
        "campo": "Matricula", 
        "ordem": 1,
        "tamanho": 20,
        "regras_de_validacao": "obrigatorio,unico"
      },
      {
        "tipo": "string",
        "campo": "Nome",
        "ordem": 2, 
        "tamanho": 200,
        "regras_de_validacao": "obrigatorio"
      },
      {
        "tipo": "string",
        "campo": "Email",
        "ordem": 3,
        "tamanho": 150,
        "regras_de_validacao": "obrigatorio,email_valido"
      }
    ]
  }'
```

## 📋 **GET - Listar Layouts**

### Resposta (resumo sem dados):
```json
{
  "count": 3,
  "results": [
    {
      "uuid": "6676add3-46dd-4c0a-9279-c833a203f600",
      "tipo_de_layout": "HABILITADOS",
      "total_campos": 29,
      "criado_em": "2025-09-04T11:09:28.849594-03:00"
    },
    {
      "uuid": "54eb3e0d-65ba-4e23-b7ee-580164ee0dc2",
      "tipo_de_layout": "VAGAS",
      "total_campos": 3,
      "criado_em": "2025-09-04T11:07:13.371479-03:00"
    },
    {
      "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "tipo_de_layout": "HABILITADOS",
      "total_campos": 3,
      "criado_em": "2025-09-08T13:30:00.000000+00:00"
    }
  ]
}
```

### cURL:
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/"
```

## 🔍 **GET - Buscar Layout Individual**

### Resposta (dados completos):
```json
{
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tipo_de_layout": "HABILITADOS",
  "dados": [
    {
      "tipo": "string",
      "campo": "Matricula",
      "ordem": 1,
      "tamanho": 20,
      "regras_de_validacao": "obrigatorio,unico"
    },
    {
      "tipo": "string",
      "campo": "Nome",
      "ordem": 2,
      "tamanho": 200,
      "regras_de_validacao": "obrigatorio"
    },
    {
      "tipo": "string",
      "campo": "Email",
      "ordem": 3,
      "tamanho": 150,
      "regras_de_validacao": "obrigatorio,email_valido"
    }
  ],
  "total_campos": 3,
  "criado_em": "2025-09-08T13:30:00.000000+00:00"
}
```

### cURL:
```bash
curl -X GET "http://localhost:8000/api/v1/layouts/a1b2c3d4-e5f6-7890-abcd-ef1234567890/"
```

## ✏️ **PUT - Atualizar Layout**

### Payload (mesma estrutura do POST):
```json
{
  "tipo_de_layout": "FUNCIONARIOS_ATUALIZADO",
  "dados": [
    {
      "tipo": "string",
      "campo": "Matricula",
      "ordem": 1,
      "tamanho": 25,
      "regras_de_validacao": "obrigatorio,unico"
    },
    {
      "tipo": "string",
      "campo": "NomeCompleto",
      "ordem": 2,
      "tamanho": 250,
      "regras_de_validacao": "obrigatorio"
    },
    {
      "tipo": "string",
      "campo": "Email",
      "ordem": 3,
      "tamanho": 150,
      "regras_de_validacao": "obrigatorio,email_valido"
    },
    {
      "tipo": "string",
      "campo": "Telefone",
      "ordem": 4,
      "tamanho": 15,
      "regras_de_validacao": "opcional"
    }
  ]
}
```

### cURL:
```bash
curl -X PUT "http://localhost:8000/api/v1/layouts/a1b2c3d4-e5f6-7890-abcd-ef1234567890/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "FUNCIONARIOS_ATUALIZADO",
    "dados": [
      {
        "tipo": "string",
        "campo": "Matricula",
        "ordem": 1,
        "tamanho": 25,
        "regras_de_validacao": "obrigatorio,unico"
      },
      {
        "tipo": "string",
        "campo": "NomeCompleto",
        "ordem": 2,
        "tamanho": 250,
        "regras_de_validacao": "obrigatorio"
      },
      {
        "tipo": "string",
        "campo": "Email",
        "ordem": 3,
        "tamanho": 150,
        "regras_de_validacao": "obrigatorio,email_valido"
      },
      {
        "tipo": "string",
        "campo": "Telefone",
        "ordem": 4,
        "tamanho": 15,
        "regras_de_validacao": "opcional"
      }
    ]
  }'
```

## 🗑️ **DELETE - Remover Layout**

### cURL:
```bash
curl -X DELETE "http://localhost:8000/api/v1/layouts/a1b2c3d4-e5f6-7890-abcd-ef1234567890/"
```

### Resposta:
```
Status: 204 No Content
```

## ⚠️ **Validações**

### Campos obrigatórios no POST/PUT:
- `tipo_de_layout` (string)
- `dados` (array com pelo menos 1 item)

### Estrutura obrigatória em cada item de `dados`:
- `ordem` (integer único)
- `campo` (string - nome do campo)
- `tipo` (string - um de: string, integer, decimal, date, text)
- `tamanho` (integer positivo)
- `regras_de_validacao` (string)

### Campos ignorados no POST/PUT:
- `uuid` (gerado automaticamente)
- `total_campos` (calculado automaticamente)
- `criado_em` (definido automaticamente)

## 📄 **Persistência**

Todos os layouts são salvos automaticamente no arquivo `data/layouts.json` quando criados/atualizados via API.

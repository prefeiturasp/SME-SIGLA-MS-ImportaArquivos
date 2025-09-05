# Status Codes de Resposta - Sistema de Importação de Arquivos

## 📊 **Status Codes Implementados**

### 🟢 **Success (2xx)**

#### `200 OK`
- **Uso**: Operações de leitura bem-sucedidas
- **Contextos**:
  - GET para listar importações
  - GET para buscar importação específica
  - PUT/PATCH para atualizar importação
  - GET para layouts e ações customizadas
- **Exemplo**: `GET /api/v1/importacao-arquivos/`

#### `201 Created`
- **Uso**: Recursos criados com sucesso
- **Contextos**:
  - POST para criar nova importação
  - POST no robust_server para salvar arquivo
- **Exemplo**: `POST /api/v1/importacao-arquivos/`

#### `204 No Content`
- **Uso**: Operação bem-sucedida sem conteúdo para retornar
- **Contextos**:
  - DELETE para remover importação
- **Exemplo**: `DELETE /api/v1/importacao-arquivos/{uuid}/`

### 🟡 **Client Error (4xx)**

#### `400 Bad Request`
- **Uso**: Dados de entrada inválidos
- **Contextos**:
  - Campos obrigatórios faltando
  - Formato de dados incorreto
  - JSON inválido
  - Conteúdo do arquivo inválido
- **Exemplo**: Upload sem arquivo ou dados malformados

#### `404 Not Found`
- **Uso**: Recurso não encontrado
- **Contextos**:
  - UUID de importação inexistente
  - UUID de layout inexistente
  - Endpoint não existente
- **Exemplo**: `GET /api/v1/importacao-arquivos/uuid-inexistente/`

#### `409 Conflict`
- **Uso**: Conflito de estado/dados
- **Contextos**:
  - Arquivo já existe no robust_server
  - Tentativa de criar recurso duplicado
- **Exemplo**: Upload de arquivo com mesmo UUID

#### `413 Payload Too Large`
- **Uso**: Arquivo muito grande
- **Contextos**:
  - Arquivo excede limite de 50MB
- **Exemplo**: Upload de arquivo > 50MB

#### `422 Unprocessable Entity`
- **Uso**: Dados válidos mas que falharam na validação de negócio
- **Contextos**:
  - Arquivo CSV não corresponde ao layout
  - Validação de campos específicos falhou
  - Headers CSV incorretos
- **Exemplo**: Arquivo VAGAS com headers de CANDIDATOS_CLASSIFICADOS

### 🔴 **Server Error (5xx)**

#### `500 Internal Server Error`
- **Uso**: Erros internos do servidor
- **Contextos**:
  - Erro ao salvar arquivo no sistema
  - Erro de conexão com banco de dados
  - Erro na comunicação com robust_server
  - Falhas não previstas

## 🔄 **Fluxos de Status Codes**

### **Fluxo 1: Upload Bem-Sucedido**
```
1. POST /api/v1/importacao-arquivos/
   └── Validação OK → 201 Created
   
2. Django → Robust Server
   └── Arquivo salvo → 201 Created
   
3. Status atualizado para "processando"
```

### **Fluxo 2: Validação Falhou**
```
1. POST /api/v1/importacao-arquivos/
   └── Headers incorretos → 422 Unprocessable Entity
   
2. Arquivo não é enviado para robust_server
```

### **Fluxo 3: Erro no Robust Server**
```
1. POST /api/v1/importacao-arquivos/
   └── Validação OK → 201 Created
   
2. Django → Robust Server
   └── Arquivo já existe → 409 Conflict
   
3. Status atualizado para "erro"
```

### **Fluxo 4: Erro de Conexão**
```
1. POST /api/v1/importacao-arquivos/
   └── Validação OK → 201 Created
   
2. Django → Robust Server
   └── Server offline → Connection Error
   
3. Status atualizado para "erro"
```

## 🧪 **Testes de Status Codes**

### **Teste 1: Sucesso**
```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -F "nome=Teste Sucesso" \
  -F "arquivo=@arquivo_valido.csv" \
  -F "tipo_de_layout=VAGAS"

# Resposta esperada: 201 Created
```

### **Teste 2: Validação de Layout**
```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -F "nome=Teste Erro Layout" \
  -F "arquivo=@arquivo_candidatos.csv" \
  -F "tipo_de_layout=VAGAS"

# Resposta esperada: 422 Unprocessable Entity
```

### **Teste 3: Arquivo Muito Grande**
```bash
curl -X POST "http://localhost:8002/api/importacao-arquivos/" \
  -d '{"uuid":"test","nome":"Teste","arquivo":{"content":"'$(base64 -w 0 arquivo_gigante.csv)'"}}'

# Resposta esperada: 413 Payload Too Large
```

### **Teste 4: JSON Inválido**
```bash
curl -X POST "http://localhost:8002/api/importacao-arquivos/" \
  -d '{"uuid":"test","nome":"Teste"'  # JSON malformado

# Resposta esperada: 400 Bad Request
```

### **Teste 5: Recurso Não Encontrado**
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/uuid-inexistente/"

# Resposta esperada: 404 Not Found
```

## 📝 **Mapeamento de Erros**

### **Django Models (Validação)**
- ValidationError → 422 Unprocessable Entity
- Arquivo inválido → 422 Unprocessable Entity
- Layout incompatível → 422 Unprocessable Entity

### **Django Views (API)**
- Serializer inválido → 400 Bad Request
- Objeto não encontrado → 404 Not Found
- ValidationError → 422 Unprocessable Entity
- Exception geral → 500 Internal Server Error

### **Robust Server (Armazenamento)**
- Campos obrigatórios faltando → 400 Bad Request
- JSON inválido → 400 Bad Request
- Base64 inválido → 400 Bad Request
- Arquivo já existe → 409 Conflict
- Arquivo muito grande → 413 Payload Too Large
- Erro ao salvar → 500 Internal Server Error

### **Integração Django ↔ Robust Server**
- ConnectionError → Status "erro" no Django
- Timeout → Status "erro" no Django
- 4xx/5xx responses → Status "erro" no Django
- 200/201 responses → Status "processando" no Django

## ✅ **Status Codes Corretos Implementados:**

- ✅ **200 OK**: Operações de leitura
- ✅ **201 Created**: Criação de recursos
- ✅ **204 No Content**: Deleção bem-sucedida
- ✅ **400 Bad Request**: Dados inválidos
- ✅ **404 Not Found**: Recurso inexistente
- ✅ **409 Conflict**: Conflito de estado
- ✅ **413 Payload Too Large**: Arquivo muito grande
- ✅ **422 Unprocessable Entity**: Validação de negócio
- ✅ **500 Internal Server Error**: Erro interno

O sistema agora usa status codes HTTP apropriados para cada situação, facilitando a integração e debugging! 🚀

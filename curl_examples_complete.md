# Exemplos de cURL para API de Importação de Arquivos - Completo

## Base URLs
```
Importação de Arquivos: http://localhost:8000/api/v1/importacao-arquivos/
Layouts: http://localhost:8000/api/v1/layouts/
```

---

## 1. LAYOUTS - Estruturas de Dados

### 1.1. Listar todos os layouts disponíveis

```bash
curl -X GET "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json"
```

### 1.2. Obter layout específico

```bash
# Layout VAGAS
curl -X GET "http://localhost:8000/api/v1/layouts/54eb3e0d-65ba-4e23-b7ee-580164ee0dc2/" \
  -H "Content-Type: application/json"

# Layout HABILITADOS  
curl -X GET "http://localhost:8000/api/v1/layouts/6676add3-46dd-4c0a-9279-c833a203f600/" \
  -H "Content-Type: application/json"
```

### 1.3. Filtrar layouts por tipo

```bash
curl -X GET "http://localhost:8000/api/v1/layouts/?tipo_de_layout=VAGAS" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/layouts/?tipo_de_layout=HABILITADOS" \
  -H "Content-Type: application/json"
```

### 1.4. Obter tipos de layout disponíveis

```bash
curl -X GET "http://localhost:8000/api/v1/layouts/tipos_disponiveis/" \
  -H "Content-Type: application/json"
```

---

## 2. IMPORTAÇÃO DE ARQUIVOS - CRUD Completo

### 2.1. Listar todas as importações

```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: application/json"
```

### 2.2. Criar importação com arquivo VAGAS

#### Primeiro, crie um arquivo CSV de exemplo para VAGAS:
```bash
cat > vagas_exemplo.csv << 'EOF'
Inscricao,Nome,DataNascimento
12345,João Silva Santos,1990-05-15
67890,Maria Oliveira Costa,1985-08-22
11111,Carlos Pereira Lima,1992-12-03
EOF
```

#### Ou crie um arquivo compatível com Excel (com BOM):
```bash
# Cria arquivo com BOM UTF-8 (compatível com Excel)
printf '\xef\xbb\xbf' > vagas_exemplo_excel.csv
cat >> vagas_exemplo_excel.csv << 'EOF'
Inscricao,Nome,DataNascimento
12345,João Silva Santos,1990-05-15
67890,Maria Oliveira Costa,1985-08-22
11111,Carlos Pereira Lima,1992-12-03
EOF
```

#### Então faça o upload (funciona com ambos os arquivos):
```bash
# Upload do arquivo normal
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "concurso=Concurso Público Municipal 2025" \
  -F "cargo=Analista Administrativo" \
  -F "arquivo=@vagas_exemplo.csv" \
  -F "tipo_de_layout=VAGAS"

# Upload do arquivo com BOM (Excel)
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "concurso=Concurso Público Estadual 2025" \
  -F "cargo=Técnico em Informática" \
  -F "arquivo=@vagas_exemplo_excel.csv" \
  -F "tipo_de_layout=VAGAS"
```

### 2.3. Criar importação com arquivo HABILITADOS

#### Primeiro, crie um arquivo CSV de exemplo:
```bash
cat > candidatos_exemplo.csv << 'EOF'
Inscricao,Nome,DataNascimento,Sexo,RG,CPF,adregistroFuncional,adNumVinculo,EndLogradouro,Numero,Complemento,Bairro,Cep,Cidade,UF,telefone,celular,Classificação,Email,Pontos,Classificação_Deficiente,Opção de Concurso,Codigo_do_Cargo,cota,Descrição_do_Cargo,Df,classNNA,ANO_do_Concurso,Observacao
123456,João Silva Santos,1990-05-15,M,123456789,12345678901,RF001,VN001,Rua das Flores,100,Apto 10,Centro,01234567,São Paulo,SP,11987654321,11987654321,1,joao@email.com,85.5,0,Opção A,CG001,Ampla,Analista de Sistemas,N,A,2024,Aprovado
789012,Maria Oliveira Costa,1985-08-22,F,987654321,98765432109,RF002,VN002,Av. Paulista,200,Sala 5,Bela Vista,87654321,São Paulo,SP,11123456789,11123456789,2,maria@email.com,82.3,1,Opção B,CG002,PCD,Coordenadora,S,B,2024,Aprovada PCD
EOF
```

#### Então faça o upload:
```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "concurso=Concurso Público Federal 2025" \
  -F "cargo=Auditor Fiscal" \
  -F "arquivo=@candidatos_exemplo.csv" \
  -F "tipo_de_layout=HABILITADOS"
```

### 2.4. Buscar importação específica

```bash
# Substitua pelo UUID retornado na criação
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/{UUID_DA_IMPORTACAO}/" \
  -H "Content-Type: application/json"
```

### 2.5. Atualizar status de uma importação

```bash
curl -X PATCH "http://localhost:8000/api/v1/importacao-arquivos/{UUID_DA_IMPORTACAO}/" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "processando"
  }'
```

### 2.6. Filtrar importações

#### Por tipo de layout:
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?tipo_de_layout=VAGAS" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?tipo_de_layout=HABILITADOS" \
  -H "Content-Type: application/json"
```

#### Por status:
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?status=pendente" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?status=processando" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?status=concluido" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?status=erro" \
  -H "Content-Type: application/json"
```

#### Combinando filtros:
```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?tipo_de_layout=VAGAS&status=pendente" \
  -H "Content-Type: application/json"
```

### 2.7. Buscar por texto

```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?search=Janeiro" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?search=candidatos" \
  -H "Content-Type: application/json"
```

### 2.8. Ordenação

```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?ordering=nome" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?ordering=-criado_em" \
  -H "Content-Type: application/json"

curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?ordering=tipo_de_layout" \
  -H "Content-Type: application/json"
```

### 2.9. Paginação

```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?page=1&page_size=5" \
  -H "Content-Type: application/json"
```

### 2.10. Formato select (para dropdowns)

```bash
curl -X GET "http://localhost:8000/api/v1/importacao-arquivos/?formato=select" \
  -H "Content-Type: application/json"
```

### 2.11. Deletar importação

```bash
curl -X DELETE "http://localhost:8000/api/v1/importacao-arquivos/{UUID_DA_IMPORTACAO}/" \
  -H "Content-Type: application/json"
```

---

## 3. VALIDAÇÃO DE ARQUIVOS

### 3.1. Teste com arquivo inválido (campos errados)

#### Crie um arquivo com campos incorretos:
```bash
cat > arquivo_invalido.csv << 'EOF'
Campo1,Campo2,Campo3
valor1,valor2,valor3
EOF
```

#### Tente fazer upload como VAGAS:
```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "nome=Teste Arquivo Inválido" \
  -F "arquivo=@arquivo_invalido.csv" \
  -F "tipo_de_layout=VAGAS"
```

**Resposta esperada:** Erro 400 com mensagem de validação

### 3.2. Teste com arquivo VAGAS mas marcado como HABILITADOS

```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "nome=Teste Tipo Incorreto" \
  -F "arquivo=@vagas_exemplo.csv" \
  -F "tipo_de_layout=HABILITADOS"
```

**Resposta esperada:** Erro 400 com mensagem de campos faltando

---

## 4. CÓDIGOS DE STATUS E TRATAMENTO DE ERROS

### 4.1. Códigos de status possíveis na criação de importações

- **201 Created**: Importação criada com sucesso
- **400 Bad Request**: Dados inválidos (campos obrigatórios ausentes, formato incorreto)
- **422 Unprocessable Entity**: Arquivo não corresponde ao layout especificado
- **503 Service Unavailable**: Servidor de processamento indisponível (erro de comunicação)
- **500 Internal Server Error**: Erro interno do servidor

### 4.2. Exemplo de erro de comunicação com servidor de processamento

```bash
# Resposta HTTP 503 Service Unavailable
{
  "error": "Serviço temporariamente indisponível",
  "message": "Erro de conexão com o servidor de processamento: Connection refused",
  "error_type": "connection_error",
  "details": "O servidor de processamento não está acessível. Tente novamente mais tarde."
}
```

### 4.3. Exemplo de erro de validação (422)

```bash
# Resposta HTTP 422 Unprocessable Entity
{
  "validation_errors": [
    "O arquivo não corresponde ao layout VAGAS. Campos obrigatórios faltando: Inscricao, Nome, DataNascimento"
  ]
}
```

### 4.4. Comportamento importante sobre salvamento

⚠️ **IMPORTANTE**: Se houver erro de comunicação com o servidor de processamento (códigos 503), **NENHUM dado será salvo** no banco de dados local. Apenas quando a comunicação for bem-sucedida os dados serão persistidos.

---

## 5. LAYOUTS - Gestão Avançada

### 4.1. Criar novo layout customizado

```bash
curl -X POST "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "VAGAS",
    "dados": [
      {
        "ordem": 1,
        "campo": "Inscricao",
        "tipo": "string",
        "tamanho": 25,
        "regras_de_validacao": "obrigatorio,unico,alfanumerico"
      },
      {
        "ordem": 2,
        "campo": "Nome",
        "tipo": "string", 
        "tamanho": 250,
        "regras_de_validacao": "obrigatorio,nome_completo"
      },
      {
        "ordem": 3,
        "campo": "DataNascimento",
        "tipo": "date",
        "tamanho": 10,
        "regras_de_validacao": "obrigatorio,data_valida,maior_18_anos"
      }
    ]
  }'
```

### 4.2. Atualizar layout existente

```bash
curl -X PUT "http://localhost:8000/api/v1/layouts/{UUID_DO_LAYOUT}/" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_de_layout": "VAGAS",
    "dados": [
      {
        "ordem": 1,
        "campo": "Inscricao",
        "tipo": "string",
        "tamanho": 30,
        "regras_de_validacao": "obrigatorio,unico"
      },
      {
        "ordem": 2,
        "campo": "Nome",
        "tipo": "string",
        "tamanho": 300,
        "regras_de_validacao": "obrigatorio"
      },
      {
        "ordem": 3,
        "campo": "DataNascimento",
        "tipo": "date",
        "tamanho": 10,
        "regras_de_validacao": "obrigatorio,data_valida"
      },
      {
        "ordem": 4,
        "campo": "Cargo",
        "tipo": "string",
        "tamanho": 100,
        "regras_de_validacao": "obrigatorio"
      }
    ]
  }'
```

### 4.3. Obter campos ordenados de um layout

```bash
curl -X GET "http://localhost:8000/api/v1/layouts/{UUID_DO_LAYOUT}/campos_ordenados/" \
  -H "Content-Type: application/json"
```

---

## 5. EXEMPLOS DE RESPOSTAS

### 5.1. Resposta da listagem de layouts:
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
      "uuid": "54eb3e0d-65ba-4e23-b7ee-580164ee0dc2",
      "tipo_de_layout": "VAGAS",
      "dados": [
        {
          "ordem": 1,
          "campo": "Inscricao",
          "tipo": "string",
          "tamanho": 20,
          "regras_de_validacao": "obrigatorio,unico"
        },
        {
          "ordem": 2,
          "campo": "Nome",
          "tipo": "string",
          "tamanho": 200,
          "regras_de_validacao": "obrigatorio"
        },
        {
          "ordem": 3,
          "campo": "DataNascimento",
          "tipo": "date",
          "tamanho": 10,
          "regras_de_validacao": "obrigatorio,data_valida"
        }
      ],
      "total_campos": 3,
      "criado_em": "2025-09-04T13:50:00Z"
    }
  ]
}
```

### 5.2. Resposta da listagem de importações:
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
      "uuid": "abc123-def456-ghi789",
      "nome": "Importação de Vagas - Janeiro 2025",
      "tipo_de_layout": "VAGAS",
      "status": "pendente",
      "criado_em": "2025-09-04T14:00:00Z"
    },
    {
      "uuid": "xyz789-uvw456-rst123",
      "nome": "Importação de Habilitados - Janeiro 2025", 
      "tipo_de_layout": "HABILITADOS",
      "status": "processando",
      "criado_em": "2025-09-04T14:05:00Z"
    }
  ]
}
```

### 5.3. Resposta de importação individual:
```json
{
  "uuid": "abc123-def456-ghi789",
  "nome": "Importação de Vagas - Janeiro 2025",
  "descricao": "Arquivo de vagas para concurso público",
  "arquivo": "/media/importacoes/vagas_exemplo.csv",
  "tipo_de_layout": "VAGAS",
  "status": "pendente",
  "criado_em": "2025-09-04T14:00:00Z",
  "atualizado_em": "2025-09-04T14:00:00Z"
}
```

### 5.4. Resposta de erro de validação:
```json
{
  "non_field_errors": [
    "O arquivo não corresponde ao layout VAGAS. Campos obrigatórios faltando: Inscricao, Nome, DataNascimento. Campos esperados: Inscricao, Nome, DataNascimento"
  ]
}
```

### 5.5. Resposta dos tipos de layout:
```json
[
  {
    "value": "VAGAS",
    "label": "Vagas"
  },
  {
    "value": "HABILITADOS", 
    "label": "Habilitados"
  }
]
```

---

## 6. COMANDOS DE TESTE E DEBUG

### 6.1. Verificar se o servidor está rodando
```bash
curl -X GET "http://localhost:8000/api/v1/" \
  -H "Content-Type: application/json"
```

### 6.2. Listar com saída formatada
```bash
curl -s -X GET "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" | python -m json.tool

curl -s -X GET "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: application/json" | python -m json.tool
```

### 6.3. Contar registros
```bash
curl -s -X GET "http://localhost:8000/api/v1/layouts/" \
  -H "Content-Type: application/json" | python -c "import sys, json; data=json.load(sys.stdin); print(f'Total de layouts: {data[\"count\"]}')"

curl -s -X GET "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: application/json" | python -c "import sys, json; data=json.load(sys.stdin); print(f'Total de importações: {data[\"count\"]}')"
```

---

## 7. ESTRUTURA DE CAMPOS

### 7.1. Layout VAGAS (3 campos):
- **Inscricao** (string, 20): obrigatorio,unico
- **Nome** (string, 200): obrigatorio  
- **DataNascimento** (date, 10): obrigatorio,data_valida

### 7.2. Layout HABILITADOS (29 campos):
1. **Inscricao** (string, 20): obrigatorio,unico
2. **Nome** (string, 200): obrigatorio
3. **DataNascimento** (date, 10): obrigatorio,data_valida
4. **Sexo** (string, 1): obrigatorio,opcoes:M,F
5. **RG** (string, 15): obrigatorio
6. **CPF** (string, 11): obrigatorio,cpf_valido
7. **adregistroFuncional** (string, 20): opcional
8. **adNumVinculo** (string, 20): opcional
9. **EndLogradouro** (string, 200): obrigatorio
10. **Numero** (string, 10): obrigatorio
11. **Complemento** (string, 50): opcional
12. **Bairro** (string, 100): obrigatorio
13. **Cep** (string, 8): obrigatorio,cep_valido
14. **Cidade** (string, 100): obrigatorio
15. **UF** (string, 2): obrigatorio,uf_valida
16. **telefone** (string, 15): opcional
17. **celular** (string, 15): opcional
18. **Classificação** (integer, 10): obrigatorio,maior_que_zero
19. **Email** (string, 150): obrigatorio,email_valido
20. **Pontos** (decimal, 10): obrigatorio,maior_ou_igual_zero
21. **Classificação_Deficiente** (integer, 10): opcional,maior_ou_igual_zero
22. **Opção de Concurso** (string, 100): obrigatorio
23. **Codigo_do_Cargo** (string, 20): obrigatorio
24. **cota** (string, 50): opcional
25. **Descrição_do_Cargo** (string, 300): obrigatorio
26. **Df** (string, 10): opcional
27. **classNNA** (string, 50): opcional
28. **ANO_do_Concurso** (integer, 4): obrigatorio,ano_valido
29. **Observacao** (text, 1000): opcional

---

## 8. TRATAMENTO DE ENCODINGS E BOM

### 8.1. Arquivos com BOM (Byte Order Mark)
O sistema agora suporta automaticamente arquivos CSV com BOM, comuns em exportações do Excel:

```bash
# Criar arquivo com BOM UTF-8
printf '\xef\xbb\xbf' > arquivo_com_bom.csv
cat >> arquivo_com_bom.csv << 'EOF'
Inscricao,Nome,DataNascimento
12345,João Silva,1990-05-15
EOF

# Upload funciona normalmente
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "nome=Arquivo com BOM" \
  -F "arquivo=@arquivo_com_bom.csv" \
  -F "tipo_de_layout=VAGAS"
```

### 8.2. Diferentes Encodings Suportados
- **UTF-8 com BOM** (`utf-8-sig`): Preferencial, remove BOM automaticamente
- **UTF-8 sem BOM** (`utf-8`): Padrão web
- **Latin-1** (`latin-1`): Fallback para arquivos antigos

### 8.3. Teste de Validação de Encoding

```bash
# Criar arquivo com caracteres especiais
cat > arquivo_acentos.csv << 'EOF'
Inscricao,Nome,DataNascimento
12345,José María Ñuñez,1990-05-15
67890,André François,1985-08-22
EOF

curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "nome=Teste Acentos" \
  -F "arquivo=@arquivo_acentos.csv" \
  -F "tipo_de_layout=VAGAS"
```

---

## 9. NOTAS IMPORTANTES

1. **Validação Rigorosa**: O arquivo deve corresponder exatamente ao layout escolhido
2. **Campos Obrigatórios**: Todos os campos definidos no layout devem estar presentes
3. **Ordem dos Campos**: A ordem no CSV deve seguir a ordem definida no layout
4. **Tipos de Arquivo**: Arquivos CSV em UTF-8, UTF-8 com BOM, ou Latin-1
5. **Tamanhos**: Respeitar os tamanhos máximos definidos para cada campo
6. **BOM Automático**: O sistema remove automaticamente o BOM dos arquivos Excel
7. **Cabeçalhos Limpos**: Espaços em branco e caracteres especiais são tratados automaticamente
8. **UUIDs Reais**: 
   - Layout VAGAS: `54eb3e0d-65ba-4e23-b7ee-580164ee0dc2`
   - Layout HABILITADOS: `6676add3-46dd-4c0a-9279-c833a203f600`

### Formatos de Arquivo Suportados:
- ✅ CSV exportado do Excel (com BOM)
- ✅ CSV padrão UTF-8 
- ✅ CSV com acentos e caracteres especiais
- ✅ CSV com espaços extras nos cabeçalhos
- ❌ Arquivos XLS/XLSX (apenas CSV)
- ❌ Arquivos com encoding inválido

Todos estes cURLs foram testados e estão funcionando no ambiente atual!

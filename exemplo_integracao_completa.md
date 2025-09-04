# Exemplo de Integração Completa - Django + Robust Server

## Como Funciona

1. **Validação**: O arquivo CSV é validado contra o layout correspondente
2. **Salvamento Local**: O arquivo é salvo no banco Django
3. **Envio Automático**: Se validado com sucesso, é enviado automaticamente para o robust_server
4. **Armazenamento Final**: O robust_server salva o arquivo na pasta `importacoes/` com nome UUID_arquivo.csv

## Pré-requisitos

```bash
# 1. Iniciar o robust_server (porta 8002)
python robust_server.py 8002 &

# 2. Iniciar o Django (porta 8000)  
python manage.py runserver 8000 &

# 3. Verificar se ambos estão funcionando
curl -s http://localhost:8002/api/health | python -m json.tool
curl -s http://localhost:8000/api/v1/layouts/ | head -20
```

## Exemplo Completo

### 1. Criar arquivo CSV de teste
```bash
cat > exemplo_vagas.csv << 'EOF'
Inscricao,Nome,DataNascimento
12345,João Silva Santos,1990-05-15
67890,Maria Oliveira Costa,1985-08-22
11111,Carlos Pereira Lima,1992-12-03
EOF
```

### 2. Fazer upload via API
```bash
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "nome=Teste Integração Completa" \
  -F "descricao=Exemplo de funcionamento completo" \
  -F "arquivo=@exemplo_vagas.csv" \
  -F "tipo_de_layout=VAGAS" \
  -F "status=pendente"
```

### 3. Resposta esperada
```json
{
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "nome": "Teste Integração Completa",
  "descricao": "Exemplo de funcionamento completo",
  "arquivo": "http://localhost:8000/importacoes/exemplo_vagas_xyz123.csv",
  "tipo_de_layout": "VAGAS",
  "status": "processando",
  "criado_em": "2025-09-04T16:30:00Z",
  "atualizado_em": "2025-09-04T16:30:00Z"
}
```

### 4. Verificar arquivo salvo pelo robust_server
```bash
# Verificar se o arquivo foi salvo com UUID
ls -la importacoes/ | grep a1b2c3d4

# Resultado esperado:
# -rw-rw-r-- 1 user user 141 Sep 4 16:30 a1b2c3d4-e5f6-7890-abcd-ef1234567890_exemplo_vagas_xyz123.csv
```

### 5. Verificar conteúdo do arquivo
```bash
cat "importacoes/a1b2c3d4-e5f6-7890-abcd-ef1234567890_exemplo_vagas_xyz123.csv"

# Resultado:
# Inscricao,Nome,DataNascimento
# 12345,João Silva Santos,1990-05-15
# 67890,Maria Oliveira Costa,1985-08-22
# 11111,Carlos Pereira Lima,1992-12-03
```

## Fluxo de Estados

1. **pendente**: Arquivo recém-criado, pronto para validação
2. **processando**: Arquivo validado e enviado com sucesso para robust_server
3. **concluido**: Processamento finalizado (manual)
4. **erro**: Erro na validação ou envio (manual)

## Validação de Arquivos

### Arquivo Válido (VAGAS)
- Cabeçalhos: `Inscricao,Nome,DataNascimento`
- Status final: `processando`

### Arquivo Inválido
```bash
# Criar arquivo com campos errados
cat > invalido.csv << 'EOF'
Campo1,Campo2,Campo3
valor1,valor2,valor3
EOF

# Tentar upload
curl -X POST "http://localhost:8000/api/v1/importacao-arquivos/" \
  -H "Content-Type: multipart/form-data" \
  -F "nome=Teste Inválido" \
  -F "arquivo=@invalido.csv" \
  -F "tipo_de_layout=VAGAS"

# Resposta de erro:
# {"non_field_errors": ["O arquivo não corresponde ao layout VAGAS..."]}
```

## Configuração

### Django (settings.py)
```python
ROBUST_SERVER_URL = os.environ.get('ROBUST_SERVER_URL', 'http://localhost:8002')
```

### Environment Variables
```bash
# .env
ROBUST_SERVER_URL=http://localhost:8002
```

## Logs e Debug

### Logs do Robust Server
O robust_server mostra logs detalhados:
```
📥 Recebendo arquivo: Teste Integração Completa
   UUID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
   Tipo: VAGAS
   Status: pendente
📁 Arquivo salvo em: /path/to/importacoes/a1b2c3d4-..._exemplo_vagas.csv
   Tamanho: 141 bytes
   Primeiras linhas do arquivo:
     1: Inscricao,Nome,DataNascimento
     2: 12345,João Silva Santos,1990-05-15
```

### Verificar Status da Integração
```bash
# Ver importações recentes
curl -s "http://localhost:8000/api/v1/importacao-arquivos/?ordering=-criado_em" | python -m json.tool

# Ver importações em processamento
curl -s "http://localhost:8000/api/v1/importacao-arquivos/?status=processando" | python -m json.tool
```

## Estrutura Final

```
importacoes/
├── a1b2c3d4-e5f6-7890-abcd-ef1234567890_exemplo_vagas_xyz123.csv
├── b2c3d4e5-f6g7-8901-bcde-f23456789012_candidatos_abc456.csv
└── c3d4e5f6-g7h8-9012-cdef-345678901234_outro_arquivo_def789.csv
```

Cada arquivo é nomeado como: `{UUID}_{nome_original_sem_espacos}.csv`

## Sucesso! ✅

O sistema agora funciona 100%:
- ✅ Validação rigorosa de arquivos CSV
- ✅ Envio automático para robust_server após validação
- ✅ Armazenamento organizado por UUID na pasta importacoes/
- ✅ Status atualizado automaticamente para "processando"
- ✅ Tratamento de erros silencioso (não quebra o fluxo principal)

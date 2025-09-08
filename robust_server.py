#!/usr/bin/env python3
"""
Servidor HTTP robusto para mock de APIs
Usando apenas a biblioteca padrão do Python
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from faker import Faker
import uuid
from datetime import datetime, timedelta
import random
import sys

# HTTP Status Constants
class HTTPStatus:
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404
    CONFLICT = 409
    PAYLOAD_TOO_LARGE = 413
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500

fake = Faker('pt_BR')  # Usar locale brasileiro

class RobustMockAPIHandler(BaseHTTPRequestHandler):
    """Handler robusto para as requisições HTTP"""
    
    def log_message(self, format, *args):
        """Custom log para mostrar as requisições"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        try:
            self.send_response(200)
            self.send_header('Content-Length', '0')
            self.send_cors_headers()
            self.end_headers()
        except Exception as e:
            print(f"Erro no OPTIONS: {e}")
            self.send_error(500, "Erro interno")
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            print(f"GET {path} - Params: {query_params}")
            
            if path == "/api/concursos":
                self.handle_concursos(query_params)
            elif path == "/api/v1/concursos":
                self.handle_concursos_v1(query_params)
            elif path == "/api/v1/candidatos/":
                self.handle_candidatos_v1()
            elif path == "/api/processos-convocacao":
                self.handle_processos(query_params)
            elif path == "/api/health":
                self.handle_health()
            elif path == "/eudes":
                self.handle_eudes()
            elif path == "/":
                self.handle_root()
            else:
                self.send_error(404, f"Endpoint não encontrado: {path}")
        except Exception as e:
            print(f"Erro no GET {self.path}: {e}")
            self.send_error(500, f"Erro interno: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            print(f"POST {path}")
            
            if path == "/api/concursos":
                self.handle_create_concurso()
            elif path == "/api/processos-convocacao":
                self.handle_create_processo()
            elif path == "/api/importacao-arquivos/":
                self.handle_receive_arquivo()
            else:
                self.send_error(404, f"Endpoint não encontrado: {path}")
        except Exception as e:
            print(f"Erro no POST {self.path}: {e}")
            self.send_error(500, f"Erro interno: {str(e)}")
    
    def send_cors_headers(self):
        """Adiciona headers CORS"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
    
    def send_json_response(self, data, status=200):
        """Envia resposta JSON de forma robusta"""
        try:
            # Converter datetime para string se necessário
            def json_serial(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            json_data = json.dumps(data, ensure_ascii=False, default=json_serial, indent=2)
            json_bytes = json_data.encode('utf-8')
            
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(json_bytes)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json_bytes)
            
            print(f"Resposta enviada: {len(json_bytes)} bytes")
            
        except Exception as e:
            print(f"Erro ao enviar resposta JSON: {e}")
            self.send_error(500, "Erro ao gerar resposta JSON")
    
    def handle_root(self):
        """Handle root endpoint"""
        response = {
            "message": "Servidor Mock API",
            "version": "1.0.0",
            "endpoints": [
                "GET /api/health",
                "GET /eudes",
                "GET /api/concursos",
                "GET /api/v1/concursos",
                "GET /api/v1/candidatos",
                "GET /api/processos-convocacao",
                "POST /api/concursos",
                "POST /api/processos-convocacao",
                "POST /api/importacao-arquivos/"
            ],
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(response)
    
    def handle_health(self):
        """Health check endpoint"""
        response = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "mock-api-server",
            "version": "1.0.0"
        }
        self.send_json_response(response)
    
    def handle_eudes(self):
        """Handle /eudes endpoint"""
        response = {}
        self.send_json_response(response, 200)
    
    def handle_concursos(self, query_params):
        """Handle /api/concursos endpoint"""
        try:
            # Gerar dados de cargos
            lista_cargos = []
            for i in range(20):
                cargo = {
                    "nome": f"Cargo {fake.job()}",
                    "uuid": str(uuid.uuid4()),
                    "id": i
                }
                lista_cargos.append(cargo)
            
            # Gerar dados de concursos
            lista_concursos = []
            for i in range(20):
                concurso = {
                    "nome": f"Concurso {fake.name()}",
                    "uuid": str(uuid.uuid4()),
                    "id": i + 1,
                    "cargos": random.choices(lista_cargos, k=random.randint(1, 3))
                }
                lista_concursos.append(concurso)
            
            # Paginação
            page = int(query_params.get('page', [1])[0])
            page_size = int(query_params.get('page_size', [10])[0])
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            results = lista_concursos[start_idx:end_idx]
            
            response = {
                "links": {
                    "next": None if end_idx >= len(lista_concursos) else f"?page={page + 1}",
                    "previous": None if page <= 1 else f"?page={page - 1}"
                },
                "count": len(lista_concursos),
                "page": page,
                "page_size": page_size,
                "results": results
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            print(f"Erro ao gerar concursos: {e}")
            self.send_error(500, f"Erro ao gerar dados: {str(e)}")
    
    def handle_concursos_v1(self, query_params):
        """Handle /api/v1/concursos endpoint - formato para frontend"""
        try:
            # Gerar dados de concursos no formato esperado pelo frontend
            lista_concursos = []
            for i in range(10):
                concurso = {
                    "id": i + 1,
                    "uuid": str(uuid.uuid4()),
                    "nome": f"Concurso {fake.company()}",
                    "descricao": fake.text(max_nb_chars=100),
                    "data_inicio": fake.date_between(start_date='-1y', end_date='today').isoformat(),
                    "data_fim": fake.date_between(start_date='today', end_date='+1y').isoformat(),
                    "status": random.choice(["ATIVO", "INATIVO", "EM_ANDAMENTO"]),
                    "vagas": random.randint(1, 50),
                    "criado_em": fake.date_time_between(start_date='-6m', end_date='now').isoformat(),
                    "atualizado_em": datetime.now().isoformat()
                }
                lista_concursos.append(concurso)
            
            self.send_json_response(lista_concursos)
            
        except Exception as e:
            print(f"Erro ao gerar concursos v1: {e}")
            self.send_error(500, f"Erro ao gerar dados: {str(e)}")
    
    def handle_candidatos_v1(self):
        """Handle /api/v1/candidatos endpoint - lista de candidatos"""
        try:
            # Lista de possíveis convocadores
            convocadores = [
                "Comissão de Seleção",
                "Diretoria de Recursos Humanos",
                "Secretaria de Administração",
                "Coordenação de Concursos",
                "Departamento de Gestão de Pessoas"
            ]
            
            # Tipos de classificação disponíveis
            tipos_classificacao = [
                "classificacao_geral",
                "classificacao_especial", 
                "classificacao_nna"
            ]
            
            # Gerar lista de 3 a 5 candidatos
            num_candidatos = random.randint(3, 5)
            lista_candidatos = []
            
            for i in range(num_candidatos):
                # Escolher aleatoriamente apenas UM tipo de classificação
                tipo_escolhido = random.choice(tipos_classificacao)
                
                candidato = {
                    "convocado_por": random.choice(convocadores),
                    "nome_candidato": fake.name()
                }
                
                # Preencher apenas o campo de classificação escolhido
                if tipo_escolhido == "classificacao_geral":
                    candidato["classificacao_geral"] = random.randint(1, 100)
                elif tipo_escolhido == "classificacao_especial":
                    candidato["classificacao_especial"] = random.randint(1, 50)
                elif tipo_escolhido == "classificacao_nna":
                    candidato["classificacao_nna"] = random.randint(1, 30)
                
                lista_candidatos.append(candidato)
            
            self.send_json_response(lista_candidatos)
            
        except Exception as e:
            print(f"Erro ao gerar candidatos v1: {e}")
            self.send_error(500, f"Erro ao gerar dados: {str(e)}")
    
    def handle_processos(self, query_params):
        """Handle /api/processos-convocacao endpoint"""
        try:
            def data_recente_aleatoria():
                hoje = datetime.now()
                dias_atras = random.randint(0, 30)
                data_aleatoria = hoje - timedelta(days=dias_atras)
                return data_aleatoria
            
            # Gerar dados de processos
            lista_processos = []
            for i in range(20):
                processo = {
                    "uuid": str(uuid.uuid4()),
                    "concurso_uuid": str(uuid.uuid4()),
                    "concurso_nome": f"Processo {fake.company()}",
                    "descricao": random.choice([
                        "DESCRICAO_CONVOCACAO",
                        "DESCRICAO_SELECAO", 
                        "DESCRICAO_AVALIACAO",
                        "DESCRICAO_CONVOCACAO_SELECAO"
                    ]),
                    "tipo_processo": random.choice([
                        "CONVOCACAO",
                        "SELECAO",
                        "AVALIACAO"
                    ]),
                    "status": random.choice([
                        "EM_ANDAMENTO",
                        "FINALIZADO", 
                        "CANCELADO"
                    ]),
                    "data_publicacao": data_recente_aleatoria().isoformat(),
                    "data_convocacao": data_recente_aleatoria().isoformat(),
                    "numero_convocados": random.randint(1, 100),
                    "criado_em": data_recente_aleatoria().isoformat(),
                    "atualizado_em": datetime.now().isoformat()
                }
                lista_processos.append(processo)
            
            # Paginação
            page = int(query_params.get('page', [1])[0])
            page_size = int(query_params.get('page_size', [10])[0])
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            results = lista_processos[start_idx:end_idx]
            
            response = {
                "links": {
                    "next": None if end_idx >= len(lista_processos) else f"?page={page + 1}",
                    "previous": None if page <= 1 else f"?page={page - 1}"
                },
                "count": len(lista_processos),
                "page": page,
                "page_size": page_size,
                "results": results
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            print(f"Erro ao gerar processos: {e}")
            self.send_error(500, f"Erro ao gerar dados: {str(e)}")
    
    def handle_create_concurso(self):
        """Handle POST /api/concursos"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                response = {
                    "uuid": str(uuid.uuid4()),
                    "nome": data.get("nome", fake.name()),
                    "id": random.randint(1000, 9999),
                    "cargos": [],
                    "created_at": datetime.now().isoformat()
                }
                
                self.send_json_response(response, 201)
            else:
                self.send_error(400, "Dados inválidos")
        except json.JSONDecodeError:
            self.send_error(400, "JSON inválido")
        except Exception as e:
            print(f"Erro ao criar concurso: {e}")
            self.send_error(500, f"Erro interno: {str(e)}")
    
    def handle_create_processo(self):
        """Handle POST /api/processos-convocacao"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                response = {
                    "uuid": str(uuid.uuid4()),
                    "concurso_uuid": data.get("concurso_uuid", str(uuid.uuid4())),
                    "concurso_nome": data.get("concurso_nome", fake.company()),
                    "descricao": data.get("descricao", "DESCRICAO_CONVOCACAO"),
                    "tipo_processo": data.get("tipo_processo", "CONVOCACAO"),
                    "status": data.get("status", "EM_ANDAMENTO"),
                    "data_publicacao": datetime.now().isoformat(),
                    "data_convocacao": datetime.now().isoformat(),
                    "numero_convocados": data.get("numero_convocados", 1),
                    "criado_em": datetime.now().isoformat(),
                    "atualizado_em": datetime.now().isoformat()
                }
                
                self.send_json_response(response, 201)
            else:
                self.send_error(400, "Dados inválidos")
        except json.JSONDecodeError:
            self.send_error(400, "JSON inválido")
        except Exception as e:
            print(f"Erro ao criar processo: {e}")
            self.send_error(500, f"Erro interno: {str(e)}")
    
    def handle_receive_arquivo(self):
        """Handle POST /api/importacao-arquivos/ - Recebe arquivo validado do sistema principal"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(HTTPStatus.BAD_REQUEST, "Content-Length requerido")
                return
                
            if content_length > 50 * 1024 * 1024:  # 50MB limite
                self.send_error(HTTPStatus.PAYLOAD_TOO_LARGE, "Arquivo muito grande (máximo 50MB)")
                return
                
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validações obrigatórias
            required_fields = ['uuid', 'concurso', 'cargo', 'tipo_de_layout', 'arquivo']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                self.send_error(HTTPStatus.BAD_REQUEST, f"Campos obrigatórios faltando: {', '.join(missing_fields)}")
                return
            
            arquivo_info = data.get('arquivo', {})
            if not arquivo_info.get('content'):
                self.send_error(HTTPStatus.BAD_REQUEST, "Conteúdo do arquivo é obrigatório")
                return
                
            print(f"📥 Recebendo arquivo:")
            print(f"   UUID: {data.get('uuid')}")
            print(f"   Concurso: {data.get('concurso', 'Não informado')}")
            print(f"   Cargo: {data.get('cargo', 'Não informado')}")
            print(f"   Tipo: {data.get('tipo_de_layout')}")
            print(f"   Status: {data.get('status')}")
                
            # Processar arquivo
            import base64
            import os
            import tempfile
            
            arquivo_info = data.get('arquivo', {})
            arquivo_nome = arquivo_info.get('name', 'arquivo.csv')
            arquivo_base64 = arquivo_info.get('content', '')
            
            try:
                # Decodificar o arquivo
                arquivo_content = base64.b64decode(arquivo_base64)
            except Exception as e:
                self.send_error(HTTPStatus.BAD_REQUEST, f"Erro ao decodificar arquivo base64: {str(e)}")
                return
                
            # Salvar na pasta importacoes (criar se não existir)
            import_dir = os.path.join(os.getcwd(), 'importacoes')
            os.makedirs(import_dir, exist_ok=True)
            
            # Nome do arquivo: uuid_concurso_cargo.csv
            uuid_arquivo = data.get('uuid', 'unknown')
            concurso_safe = data.get('concurso', 'concurso').replace(' ', '_').replace('/', '_')[:30]
            cargo_safe = data.get('cargo', 'cargo').replace(' ', '_').replace('/', '_')[:30]
            arquivo_path = os.path.join(import_dir, f"{uuid_arquivo}_{concurso_safe}_{cargo_safe}.csv")
            
            # Verificar se arquivo já existe (conflito)
            if os.path.exists(arquivo_path):
                self.send_error(HTTPStatus.CONFLICT, f"Arquivo já existe: {os.path.basename(arquivo_path)}")
                return
            
            # Tentar salvar o arquivo
            try:
                with open(arquivo_path, 'wb') as f:
                    f.write(arquivo_content)
                
                print(f"📁 Arquivo salvo em: {arquivo_path}")
                print(f"   Tamanho: {len(arquivo_content)} bytes")
            except IOError as e:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Erro ao salvar arquivo: {str(e)}")
                return
            except OSError as e:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Erro do sistema ao salvar arquivo: {str(e)}")
                return
            
            # Processar arquivo salvo (ler algumas linhas para log)
            linhas = []
            try:
                with open(arquivo_path, 'r', encoding='utf-8-sig') as f:
                    linhas = f.readlines()[:5]  # Primeiras 5 linhas
                    print(f"   Primeiras linhas do arquivo:")
                    for i, linha in enumerate(linhas):
                        print(f"     {i+1}: {linha.strip()}")
            except Exception as e:
                print(f"   Erro ao ler arquivo: {e}")
                # Não falhar por causa de erro de leitura
                
            # Resposta de sucesso
            response = {
                "uuid": data.get('uuid'),
                "status": "recebido_com_sucesso",
                "concurso": data.get('concurso'),
                "cargo": data.get('cargo'),
                "tipo_de_layout": data.get('tipo_de_layout'),
                "arquivo": {
                    "path": arquivo_path,
                    "tamanho": len(arquivo_content),
                    "nome_original": arquivo_nome
                },
                "processamento": {
                    "total_linhas": len(linhas),
                    "primeira_linha": linhas[0].strip() if linhas else None,
                    "status": "salvo_na_pasta_importacoes"
                },
                "metadata": {
                    "recebido_em": datetime.now().isoformat(),
                    "processado_por": "robust_server",
                    "fonte": data.get('metadata', {}).get('fonte', 'unknown'),
                    "diretorio": import_dir
                },
                "message": f"Arquivo '{data.get('nome')}' recebido e salvo em importacoes/ com sucesso!"
            }
            
            # Status 201 Created - arquivo criado com sucesso
            self.send_json_response(response, HTTPStatus.CREATED)
                
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "JSON inválido")
        except Exception as e:
            print(f"Erro ao receber arquivo: {e}")
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Erro interno: {str(e)}")


def run_server(port=8002):
    """Inicia o servidor HTTP"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, RobustMockAPIHandler)
    
    print(f"🚀 Servidor mock robusto rodando em http://localhost:{port}")
    print(f"📊 Endpoints disponíveis:")
    print(f"   GET  /")
    print(f"   GET  /api/health")
    print(f"   GET  /eudes")
    print(f"   GET  /api/concursos")
    print(f"   GET  /api/v1/concursos")
    print(f"   GET  /api/v1/candidatos")
    print(f"   GET  /api/processos-convocacao")
    print(f"   POST /api/concursos")
    print(f"   POST /api/processos-convocacao")
    print(f"   POST /api/importacao-arquivos/ (recebe arquivos validados)")
    print(f"🔧 Pressione Ctrl+C para parar")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado")
        httpd.server_close()


if __name__ == "__main__":
    # Porta padrão ou da linha de comando
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    
    run_server(port)

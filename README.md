# 🔮 Oráculo — Plataforma Universal de Inteligência Corporativa

**Oráculo** é uma plataforma enterprise de inteligência sobre dados — conecta qualquer fonte de dados, entende o contexto de negócio automaticamente, responde perguntas em linguagem natural, detecta anomalias, gera insights proativos e executa ações autônomas.

> Posicionamento: concorrente de Palantir / Databricks / Snowflake. Não é um chatbot.

---

## ✨ Capacidades

| Módulo | O que faz |
|---|---|
| **Semantic Engine** | Classifica automaticamente qualquer dataset em domínio de negócio (Financeiro, RH, CRM, Logística, etc.) |
| **Universal Connectors** | Conecta CSV, Excel, JSON, Parquet, PDF/DOCX, PostgreSQL, MySQL, SQLite |
| **Metadata Catalog** | Schema discovery automático, profiling estatístico, score de qualidade A–F |
| **NL2SQL** | Transforma perguntas em português em SQL válido e seguro, executado via DuckDB |
| **Hybrid RAG** | Combina busca vetorial (FAISS) em documentos + NL2SQL em dados estruturados |
| **AI Data Analyst** | Gera KPIs, detecta anomalias e produz executive summary ao conectar uma fonte |
| **Agent Actions** | Planeja e executa ações autônomas: alertas, relatórios, notificações |
| **Knowledge Graph** | Extrai entidades e relações dos dados, constrói grafo navegável |

---

## 🏗️ Arquitetura

```
Oráculo/
├── backend/                    # FastAPI (Python 3.11)
│   ├── api/                   # Routers, middlewares, config
│   ├── catalog/               # Semantic Engine, Registry, Profiler, Quality
│   ├── connectors/            # 8 conectores (files + databases)
│   ├── nl2sql/                # Engine, Validator, Executor (DuckDB), Router
│   ├── rag/                   # VectorStore (FAISS), DocumentIndexer, HybridRetriever
│   ├── analyst/               # KPIGenerator, AnomalyDetector, InsightEngine
│   ├── actions/               # ActionPlanner, ActionRegistry, Builtins
│   ├── graph/                 # EntityExtractor, RelationBuilder, KnowledgeGraph
│   ├── core/                  # LLMClient (Anthropic/OpenAI), logging_config
│   ├── db/                    # SQLAlchemy models (PostgreSQL/SQLite), Alembic
│   ├── scripts/               # migrate_json_to_pg.py
│   ├── tests/                 # pytest suite (auth, nl2sql, connectors)
│   └── requirements.prod.txt  # Dependências consolidadas
│
├── frontend/                   # React 18 + Vite + TailwindCSS
│   └── src/
│       ├── pages/             # Chat, DataSources, Analytics, Alerts, Graph, Settings
│       ├── services/api.ts    # Axios client com JWT interceptor
│       └── contexts/          # Auth, Chat, Theme
│
├── Dockerfile.backend          # Python 3.11, non-root user
├── Dockerfile.frontend         # Node 20 build → nginx
├── docker-compose.yml          # backend + frontend + postgres + redis
├── deploy/nginx.conf           # SPA fallback + proxy /api/
├── .env.example                # Variáveis necessárias
└── legacy/                     # Código legado (Streamlit, logística) — não usado
```

**Stack:**
- Backend: FastAPI 0.109 · Python 3.11 · SQLAlchemy 2 · Alembic
- Frontend: React 18 · Vite · TailwindCSS · Recharts
- LLM: Anthropic Claude (primário) · OpenAI GPT-4o (fallback)
- Vector store: FAISS per-source (TF-IDF fallback sem API key)
- Database: PostgreSQL (produção) · SQLite (desenvolvimento)
- Auth: JWT HS256 · passlib sha256_crypt

---

## 🚀 Início Rápido

### Opção 1 — Docker (recomendado para produção)

```bash
# 1. Configurar variáveis
cp .env.example .env
# Preencher: SECRET_KEY, POSTGRES_PASSWORD, ANTHROPIC_API_KEY ou OPENAI_API_KEY

# 2. Subir todos os serviços
docker-compose up --build

# 3. (Opcional) Migrar dados existentes de JSON → PostgreSQL
docker-compose exec backend python scripts/migrate_json_to_pg.py
```

Acesse: **http://localhost** (frontend) · **http://localhost:5000/docs** (API)

---

### Opção 2 — Desenvolvimento local

**Pré-requisitos:** Python 3.11+, Node 20+

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.prod.txt
cp ../.env.example ../.env   # preencher vars
uvicorn api.main:app --reload --port 5000

# Frontend (outro terminal)
cd frontend
npm install
npm run dev
```

Acesse: **http://localhost:5173**

**Credenciais padrão:** `admin` / `admin123`

---

## ⚙️ Configuração

Copie `.env.example` para `.env` e preencha:

```env
# Obrigatório — gerar com: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=

# LLM — pelo menos um é necessário
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Banco de dados (PostgreSQL em produção, SQLite é criado automaticamente em dev)
DATABASE_URL=postgresql://oraculo:senha@localhost:5432/oraculo
POSTGRES_PASSWORD=

# Ambiente
ENVIRONMENT=development   # development | production
```

---

## 🔌 API — Endpoints Principais

```http
# Autenticação
POST /api/auth/login          { "username": "admin", "password": "admin123" }

# Fontes de dados
GET  /api/datasources         Lista todas as fontes
POST /api/datasources/register Registra nova fonte (DB)
POST /api/datasources/upload   Upload de arquivo (CSV, Excel, PDF...)
POST /api/datasources/{id}/connect  Conecta e descobre schema

# Inteligência
POST /api/query               Pergunta universal (NL2SQL + RAG roteado)
POST /api/datasources/{id}/analyze  KPIs + anomalias + executive summary
POST /api/datasources/{id}/act      Agent Actions
GET  /api/datasources/{id}/graph    Knowledge Graph

# Sistema
GET  /api/health              Status real de todos os subsistemas
GET  /api/ping                Liveness probe
```

Documentação interativa: **http://localhost:5000/docs**

---

## 🧪 Testes

```bash
cd backend
pip install -r requirements.test.txt
pytest                    # Todos os testes
pytest tests/test_auth.py       # Somente autenticação
pytest tests/test_nl2sql.py     # Somente NL2SQL
pytest --cov --cov-report=html  # Com cobertura
```

**Cobertura mínima configurada: 60%**

---

## 🔒 Segurança

- **JWT obrigatório** em todas as rotas (`REQUIRE_AUTH=True`)
- **Middleware valida assinatura e expiração** do token a cada request
- **SECRET_KEY** deve ser definida via env — sistema avisa e usa chave efêmera se ausente
- **Falha rápida em produção** se `SECRET_KEY` não configurada
- **Senhas mascaradas** nas respostas da API (nunca expostas)
- **SQL injection** bloqueado no `SQLValidator` antes de qualquer execução
- **Trace ID** em todos os requests (`X-Trace-ID`) para auditoria

---

## 📊 Connectors Disponíveis

| Conector | Tipo | Status |
|---|---|---|
| CSV | Arquivo | ✅ |
| Excel (XLSX/XLS) | Arquivo | ✅ |
| JSON | Arquivo | ✅ |
| Parquet | Arquivo | ✅ |
| PDF / DOCX / TXT | Documento | ✅ |
| PostgreSQL | Banco | ✅ |
| MySQL / MariaDB | Banco | ✅ |
| SQLite | Banco | ✅ |
| MongoDB | Banco | 🔜 |
| Amazon S3 | Cloud | 🔜 |
| REST API genérica | Cloud | 🔜 |

---

## 📝 Changelog

### v4.0.0 — Hardening & Production-Ready
- 🔒 Autenticação JWT real ativada (middleware com validação de assinatura)
- 🐳 Docker completo: backend + frontend + PostgreSQL + Redis
- 🗄️ SQLAlchemy + Alembic: migração de JSON files para PostgreSQL
- 🧪 Suite de testes: auth, NL2SQL, connectors, semantic engine
- 📊 Structured logging (JSON em produção, trace IDs por request)
- 🏥 Health check real: LLM, vector store, DB, catalog, auth
- 🧹 Código legado isolado em `legacy/`

### v3.0.0 — Feature Complete (Sprints 0–7)
- ⚙️ Universal Semantic Engine (10 domínios de negócio)
- 🔌 8 Universal Connectors (arquivos + bancos de dados)
- 📚 Metadata Catalog (schema discovery, profiling, quality score)
- 🗣️ NL2SQL com validação e execução DuckDB
- 🔍 Hybrid RAG (FAISS per-source + document indexer)
- 🤖 AI Data Analyst (KPIs, anomalias, executive summary)
- ⚡ Agent Actions (planner, alertas, relatórios)
- 🕸️ Knowledge Graph (NetworkX, entity extraction, relation building)
- ⚛️ Frontend React completo (6 páginas conectadas ao backend)

### v2.x — GPTRACKER (legado, ver `legacy/`)

---

**Oráculo v4.0** — Transformando qualquer dado em inteligência corporativa acionável 🔮
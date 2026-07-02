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
| **Agent Actions** | Planeja e executa ações autônomas: alertas, relatórios, notificações, e-mails |
| **Knowledge Graph** | Extrai entidades e relações dos dados, constrói grafo navegável (NetworkX) |

---

## 🏗️ Arquitetura

```
Oráculo/
├── backend/                        # FastAPI (Python 3.11+)
│   ├── api/                        # Routers, middlewares, config, auth
│   │   ├── routers/               # auth, chat, datasources, query, analytics,
│   │   │                          #   files, export, health, models
│   │   ├── middleware.py          # AuthMiddleware + TraceMiddleware
│   │   ├── auth_service.py        # JWT, hash de senhas (passlib)
│   │   ├── config.py              # Settings centralizadas
│   │   └── conversation_store.py  # Persistência de conversas
│   ├── catalog/                    # Semantic Engine, Registry, Profiler, Quality
│   ├── connectors/                 # Universal Connectors
│   │   ├── files/                 # CSV, Excel, JSON, Parquet, Document
│   │   └── databases/             # PostgreSQL, MySQL, SQLite
│   ├── nl2sql/                     # Engine, Validator, Executor (DuckDB), Router
│   ├── rag/                        # VectorStore (FAISS), DocumentIndexer, HybridRetriever
│   ├── analyst/                    # KPIGenerator, AnomalyDetector, InsightEngine
│   ├── actions/                    # ActionPlanner, ActionRegistry, Builtins
│   │   └── builtin/               # create_alert, generate_report, send_email
│   ├── graph/                      # EntityExtractor, RelationBuilder, KnowledgeGraph
│   ├── core/                       # LLMClient, ModelConfig, LoggingConfig
│   ├── db/                         # SQLAlchemy models (PostgreSQL/SQLite), Alembic
│   ├── scripts/                    # migrate_json_to_pg.py
│   ├── tests/                      # pytest (auth, nl2sql, connectors, llm_client, models)
│   └── requirements.prod.txt       # Dependências consolidadas
│
├── frontend/                       # React 18 + Vite + TailwindCSS
│   └── src/
│       ├── pages/                  # Login, Chat, DataSources, Analytics,
│       │                           #   Alerts, Graph, Models, Settings
│       ├── components/             # Header, Sidebar, ChatMessage, ConversationList,
│       │                           #   ProtectedRoute, QuickActions, etc.
│       ├── services/api.ts         # Axios client com JWT interceptor
│       ├── contexts/               # Auth, Chat, Theme
│       └── types/                  # TypeScript types
│
├── Dockerfile.backend              # Python 3.11, non-root user
├── Dockerfile.frontend             # Node 20 build → nginx
├── docker-compose.yml              # backend + frontend + postgres + redis
├── deploy/nginx.conf               # SPA fallback + proxy /api/
├── .env.example                    # Variáveis necessárias
└── legacy/                         # Código legado (Streamlit, GPTRACKER) — não usado
```

### Stack

- **Backend:** FastAPI 0.109 · Python 3.11+ · SQLAlchemy 2 · Alembic · DuckDB
- **Frontend:** React 18 · Vite 5 · TailwindCSS · Recharts · Zustand · Framer Motion
- **LLM:** 4 providers suportados (ver seção [🤖 LLM Providers](#-llm-providers))
- **Vector store:** FAISS per-source (TF-IDF fallback sem API key)
- **Database:** PostgreSQL 16 (produção) · SQLite (desenvolvimento)
- **Cache/Filas:** Redis 7
- **Auth:** JWT HS256 · passlib bcrypt
- **Graph:** NetworkX 3

---

## 🤖 LLM Providers

O Oráculo suporta **4 providers de LLM** com seleção automática ou forçada via env var `LLM_PROVIDER`:

| Provider | Env Var | Endpoint | Modelos | Prioridade |
|---|---|---|---|---|
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | API nativa Anthropic | Claude 3.5 Sonnet, etc. | 1ª (auto) |
| **OpenAI GPT** | `OPENAI_API_KEY` | API nativa OpenAI | GPT-4o, GPT-4 Turbo, etc. | 2ª (auto) |
| **OpenCode Zen** | `OPENCODE_API_KEY` | `https://opencode.ai/zen/v1` | `opencode/<model-id>` | 3ª (auto) |
| **Z.AI** | `ZAI_API_KEY` | `https://api.z.ai/api/paas/v4` | GLM-4.5, GLM-5 | 4ª (auto) |

**Seleção automática:** o primeiro provider com API key configurada é usado.

**Forçar um provider específico:**
```env
LLM_PROVIDER=zai        # zai | anthropic | openai | opencode | auto
```

O cliente unificado (`backend/core/llm_client.py`) é usado por todos os módulos: NL2SQL, Semantic Engine, Chat, AI Data Analyst, Agent Actions e Knowledge Graph.

O usuário também pode trocar o modelo ativo em runtime via página **Models** no frontend — a escolha é persistida em `DATA_DIR/active_model.json`.

---

## 🚀 Início Rápido

### Opção 1 — Docker (recomendado para produção)

```bash
# 1. Configurar variáveis
cp .env.example .env
# Preencher: SECRET_KEY, POSTGRES_PASSWORD, e pelo menos uma API key de LLM

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
# ── Obrigatório ────────────────────────────────────────────
# Gerar com: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=

# ── LLM (pelo menos um é necessário) ───────────────────────
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OPENCODE_API_KEY=
OPENCODE_BASE_URL=https://opencode.ai/zen/v1
ZAI_API_KEY=
ZAI_BASE_URL=https://api.z.ai/api/paas/v4
LLM_PROVIDER=auto              # auto | anthropic | openai | opencode | zai

# ── Banco de dados ─────────────────────────────────────────
# PostgreSQL em produção; SQLite criado automaticamente em dev
DATABASE_URL=postgresql://oraculo:senha@localhost:5432/oraculo
POSTGRES_DB=oraculo
POSTGRES_USER=oraculo
POSTGRES_PASSWORD=

# ── Redis ──────────────────────────────────────────────────
REDIS_URL=redis://:senha@localhost:6379/0

# ── Ambiente ───────────────────────────────────────────────
ENVIRONMENT=development        # development | staging | production
LOG_LEVEL=INFO                 # DEBUG | INFO | WARNING | ERROR
```

---

## 🔌 API — Endpoints Principais

```http
# Autenticação
POST /api/auth/login          { "username": "admin", "password": "admin123" }

# Fontes de dados
GET  /api/datasources          Lista todas as fontes
POST /api/datasources/register Registra nova fonte (DB)
POST /api/datasources/upload   Upload de arquivo (CSV, Excel, PDF...)
POST /api/datasources/{id}/connect  Conecta e descobre schema

# Inteligência
POST /api/query                Pergunta universal (NL2SQL + RAG roteado)
POST /api/datasources/{id}/analyze  KPIs + anomalias + executive summary
POST /api/datasources/{id}/act      Agent Actions
GET  /api/datasources/{id}/graph    Knowledge Graph

# Modelos LLM
GET  /api/models               Lista modelos disponíveis do provider ativo
POST /api/models/active        Define modelo ativo em runtime

# Sistema
GET  /api/health               Status real de todos os subsistemas
GET  /api/ping                 Liveness probe
```

Documentação interativa: **http://localhost:5000/docs**

---

## 🧪 Testes

```bash
cd backend
pip install -r requirements.test.txt
pytest                          # Todos os testes
pytest tests/test_auth.py       # Somente autenticação
pytest tests/test_nl2sql.py     # Somente NL2SQL
pytest tests/test_connectors.py # Somente conectores
pytest tests/test_llm_client.py # Somente LLM client
pytest --cov --cov-report=html  # Com cobertura
```

**Cobertura mínima configurada: 60%**

---

## 🔒 Segurança

- **JWT obrigatório** em todas as rotas (`REQUIRE_AUTH=True`)
- **Middleware valida assinatura e expiração** do token a cada request
- **SECRET_KEY** deve ser definida via env — sistema avisa e usa chave efêmera se ausente
- **Falha rápida em produção** se `SECRET_KEY` não configurada
- **Senhas com hash bcrypt** — nunca expostas nas respostas da API
- **SQL injection** bloqueado no `SQLValidator` antes de qualquer execução
- **Trace ID** em todos os requests (`X-Trace-ID`) para auditoria
- **Structured logging** — JSON em produção, formato legível em desenvolvimento

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

## �️ Frontend — Páginas

| Página | Descrição |
|---|---|
| **Login** | Autenticação com JWT |
| **Chat** | Conversa com IA (NL2SQL + RAG), histórico de conversas |
| **Data Sources** | Registro e upload de fontes, descoberta de schema |
| **Analytics** | KPIs, gráficos, detecção de anomalias |
| **Alerts** | Alertas gerados pelo Agent Actions |
| **Graph** | Visualização do Knowledge Graph |
| **Models** | Seleção de modelo LLM ativo em runtime |
| **Settings** | Health check dos subsistemas, configurações |

---

## 🐳 Deploy com Docker

```bash
# 1. Configurar .env (ver seção ⚙️ Configuração)
cp .env.example .env

# 2. Build e subir
docker-compose up --build

# 3. Migrar schema do banco (Alembic)
docker-compose exec backend alembic upgrade head

# 4. (Opcional) Migrar dados JSON legados para PostgreSQL
docker-compose exec backend python scripts/migrate_json_to_pg.py
```

**Serviços:**
- Frontend (nginx): porta 80
- Backend (uvicorn): porta 5000
- PostgreSQL 16: porta 5432
- Redis 7: porta 6379

---

## �📝 Changelog

### v4.0.0 — Hardening & Production-Ready
- 🔒 Autenticação JWT real ativada (middleware com validação de assinatura)
- 🐳 Docker completo: backend + frontend + PostgreSQL 16 + Redis 7
- 🗄️ SQLAlchemy + Alembic: migração de JSON files para PostgreSQL
- 🧪 Suite de testes: auth, NL2SQL, connectors, LLM client, models
- 📊 Structured logging (JSON em produção, trace IDs por request)
- 🏥 Health check real: LLM, vector store, DB, catalog, auth
- 🤖 Suporte a 4 LLM providers: Anthropic, OpenAI, OpenCode Zen, Z.AI
- 🎛️ Seleção de modelo ativo em runtime (página Models)
- 🧹 Código legado isolado em `legacy/`

### v3.0.0 — Feature Complete (Sprints 0–7)
- ⚙️ Universal Semantic Engine (10 domínios de negócio)
- 🔌 8 Universal Connectors (arquivos + bancos de dados)
- 📚 Metadata Catalog (schema discovery, profiling, quality score)
- 🗣️ NL2SQL com validação e execução DuckDB
- 🔍 Hybrid RAG (FAISS per-source + document indexer)
- 🤖 AI Data Analyst (KPIs, anomalias, executive summary)
- ⚡ Agent Actions (planner, alertas, relatórios, e-mails)
- 🕸️ Knowledge Graph (NetworkX, entity extraction, relation building)
- ⚛️ Frontend React completo (8 páginas conectadas ao backend)

### v2.x — GPTRACKER (legado, ver `legacy/`)

---

## 📄 Licença

MIT

---

**Oráculo v4.0** — Transformando qualquer dado em inteligência corporativa acionável 🔮
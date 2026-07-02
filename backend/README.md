# 🔮 Oráculo — Backend

Backend FastAPI do Oráculo — Plataforma Universal de Inteligência Corporativa.

---

## 🚀 Tecnologias

- **Python 3.11+**
- **FastAPI 0.109** — API REST assíncrona
- **SQLAlchemy 2 + Alembic** — ORM e migrações (PostgreSQL / SQLite)
- **DuckDB** — Engine SQL em memória para fontes de arquivo
- **FAISS** — Vector store para Hybrid RAG
- **NetworkX** — Knowledge Graph
- **passlib bcrypt + python-jose** — JWT auth
- **structlog** — Structured logging

### LLM Providers (4 suportados)

| Provider | Env Var | Endpoint |
|---|---|---|
| Anthropic Claude | `ANTHROPIC_API_KEY` | API nativa |
| OpenAI GPT | `OPENAI_API_KEY` | API nativa |
| OpenCode Zen | `OPENCODE_API_KEY` | `https://opencode.ai/zen/v1` |
| Z.AI | `ZAI_API_KEY` | `https://api.z.ai/api/paas/v4` |

Seleção automática por prioridade ou forçada via `LLM_PROVIDER`.

---

## 📦 Instalação

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.prod.txt
```

---

## 🎯 Estrutura

```
backend/
├── api/                           # FastAPI app
│   ├── main.py                   # Entry point, CORS, lifespan
│   ├── config.py                 # Settings centralizadas
│   ├── models.py                 # Pydantic schemas
│   ├── middleware.py             # AuthMiddleware + TraceMiddleware
│   ├── auth_service.py           # JWT, hash de senhas, users
│   ├── dependencies.py           # Injeção de dependências
│   ├── conversation_store.py     # Persistência de conversas
│   ├── file_processor.py         # Processamento de uploads
│   ├── llm_service.py            # Serviço LLM (legado, não usado pelo chat)
│   ├── rag_service.py            # RAG legado (não usado pelo chat)
│   └── routers/                  # Endpoints REST
│       ├── auth.py               # POST /login, GET /me
│       ├── chat.py               # Chat com QueryRouter + HybridRetriever
│       ├── datasources.py        # CRUD de fontes, connect, analyze, act, graph
│       ├── query.py              # Query universal (NL2SQL + RAG)
│       ├── analytics.py          # Analytics e KPIs
│       ├── files.py              # Upload e processamento de arquivos
│       ├── export.py             # Exportação (CSV, Excel, PDF)
│       ├── health.py             # Health check real
│       └── models.py             # Lista e seleciona modelos LLM
│
├── catalog/                       # Metadata Catalog
│   ├── semantic_engine.py        # Classificação automática de domínio
│   ├── schema_discovery.py       # Descoberta de schema
│   ├── profiler.py               # Profiling estatístico
│   ├── quality_scorer.py         # Score de qualidade A–F
│   └── registry.py               # Registry de fontes
│
├── connectors/                    # Universal Connectors
│   ├── base.py                   # Interface base
│   ├── files/                    # CSV, Excel, JSON, Parquet, Document
│   └── databases/                # PostgreSQL, MySQL, SQLite
│
├── nl2sql/                        # Natural Language to SQL
│   ├── engine.py                 # Geração de SQL via LLM
│   ├── validator.py              # Validação de segurança (SQL injection)
│   ├── executor.py               # Execução via DuckDB
│   └── router.py                 # Roteamento de queries
│
├── rag/                           # Hybrid RAG
│   ├── vector_store.py           # FAISS per-source
│   ├── document_indexer.py       # Indexação de documentos
│   └── hybrid_retriever.py       # Retrieval híbrido (vetorial + NL2SQL)
│
├── analyst/                       # AI Data Analyst
│   ├── kpi_generator.py          # Geração automática de KPIs
│   ├── anomaly_detector.py       # Detecção de anomalias
│   └── insight_engine.py         # Executive summary + insights
│
├── actions/                       # Agent Actions
│   ├── base.py                   # Interface de ações
│   ├── planner.py                # Planejamento de ações via LLM
│   ├── registry.py               # Registro de ações
│   └── builtin/                  # Ações nativas
│       ├── create_alert.py       # Criar alerta
│       ├── generate_report.py    # Gerar relatório
│       └── send_email.py         # Enviar e-mail
│
├── graph/                         # Knowledge Graph
│   ├── entity_extractor.py       # Extração de entidades via LLM
│   ├── relation_builder.py       # Construção de relações
│   ├── knowledge_graph.py        # API do grafo
│   └── graph_store.py            # Persistência (NetworkX)
│
├── core/                          # Core utilities
│   ├── llm_client.py             # Cliente unificado (Anthropic/OpenAI/OpenCode/Z.AI)
│   ├── model_config.py           # Modelo ativo persistido
│   └── logging_config.py         # Structured logging
│
├── db/                            # Database
│   ├── engine.py                 # SQLAlchemy async engine
│   └── models.py                 # UserModel, DataSourceModel, AlertModel
│
├── alembic/                       # Migrações
│   └── versions/                 # 0001_initial_schema
│
├── scripts/                       # Scripts
│   └── migrate_json_to_pg.py     # Migra JSON legado → PostgreSQL
│
├── tests/                         # Testes (pytest)
│   ├── conftest.py               # Fixtures (auth, CSV, Excel, app_client)
│   ├── test_auth.py              # Hash, JWT, login, rotas protegidas
│   ├── test_nl2sql.py            # SQLValidator, SQLExecutor, QueryRouter
│   ├── test_connectors.py        # CSV, Excel, JSON, SemanticEngine
│   ├── test_llm_client.py        # LLM client unificado
│   └── test_models.py            # API de modelos
│
├── pytest.ini                     # asyncio_mode=auto, coverage 60%
├── requirements.prod.txt          # Dependências consolidadas
└── requirements.test.txt          # pytest-asyncio, httpx, aiosqlite
```

---

## 🚀 Executar

```bash
# Desenvolvimento
source venv/bin/activate
uvicorn api.main:app --reload --port 5000

# Ou via script
python run_api.py
```

Acessar:
- **API:** http://localhost:5000
- **Docs Swagger:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc

---

## 🔧 Variáveis de Ambiente

Ver arquivo `.env.example` na raiz do projeto. Principais:

```env
SECRET_KEY=                    # Obrigatório (gerar com secrets.token_hex(32))
ANTHROPIC_API_KEY=             # LLM provider 1
OPENAI_API_KEY=                # LLM provider 2
OPENCODE_API_KEY=              # LLM provider 3
ZAI_API_KEY=                   # LLM provider 4
LLM_PROVIDER=auto              # auto | anthropic | openai | opencode | zai
DATABASE_URL=                  # PostgreSQL (produção) ou SQLite (dev)
ENVIRONMENT=development        # development | production
```

---

## 🧪 Testes

```bash
pip install -r requirements.test.txt
pytest                              # Todos os testes
pytest tests/test_auth.py           # Autenticação
pytest tests/test_nl2sql.py         # NL2SQL
pytest tests/test_connectors.py     # Connectors
pytest tests/test_llm_client.py     # LLM client
pytest --cov --cov-report=html      # Com cobertura
```

---

## �️ Migrações (Alembic)

```bash
# Aplicar migrações
alembic upgrade head

# Criar nova migração
alembic revision --autogenerate -m "descrição"

# Rollback
alembic downgrade -1
```

---

## � Arquitetura de Chat (v4)

O chat (`api/routers/chat.py`) usa a arquitetura unificada:

1. **QueryRouter** — decide se a pergunta vai para NL2SQL (dados estruturados) ou RAG (documentos)
2. **HybridRetriever** — executa retrieval híbrido combinando busca vetorial + NL2SQL
3. **LLMClient** — gera a resposta final usando o provider ativo

Os módulos legados `llm_service.py` e `rag_service.py` **não são mais usados** pelo chat.

---

## 📝 Licença

MIT

---

**🔮 Oráculo Backend v4.0** — FastAPI · Python 3.11+

# 01 — STATUS ATUAL DO PROJETO ORÁCULO
> Auditoria realizada em: 22/06/2026  
> Baseada em análise completa do código-fonte — sem suposições.

---

## VISÃO GERAL

O Oráculo é uma plataforma de inteligência corporativa baseada em FastAPI (backend Python) e React/TypeScript (frontend). O projeto partiu de um chatbot especializado em logística/comércio e está sendo transformado em uma Plataforma Universal de Inteligência de Dados (concorrente de Palantir/Databricks).

**Stack real em produção:**
| Camada | Tecnologia |
|---|---|
| Backend | FastAPI 0.109 + Python 3.x |
| Frontend | React 18 + Vite + TailwindCSS |
| LLM | Anthropic Claude Haiku-4-5 (primário) / OpenAI GPT-4o (fallback) |
| Vector Store | FAISS (per-source, TF-IDF fallback) |
| Persistência | JSON files (registry, users, alerts) |
| Banco de dados | Nenhum (sem PostgreSQL, sem Redis) |
| Orquestração | Nenhuma (sem LangGraph, sem Docker) |
| Auth | JWT (sha256_crypt) + JSON file |

---

## ESTRUTURA DE ARQUIVOS VERIFICADA

### Backend (`/backend`)
```
api/              ← FastAPI app, routers, middleware
  main.py         ← Entry point
  auth_service.py ← JWT + usuários (JSON file)
  llm_service.py  ← SimpleLLMService (OpenAI direto, legado)
  rag_service.py  ← RAGService legado (FAISS global, não por fonte)
  config.py       ← Settings (pydantic-settings)
  middleware.py   ← Logging + Auth (AuthMiddleware NOT ativo: REQUIRE_AUTH=False)
  routers/
    auth.py       ← Login, register, me
    chat.py       ← /chat, histórico
    analytics.py  ← Stub mínimo
    files.py      ← Upload legado
    health.py     ← Health check
    datasources.py← CRUD + connect + analyze + act + graph (Sprint 1–7)
    query.py      ← NL2SQL + RAG routing (Sprint 3–4)

connectors/       ← Sprint 1
  base.py         ← Interfaces abstratas
  files/          ← csv, excel, json, parquet, document
  databases/      ← postgres, mysql, sqlite

catalog/          ← Sprint 0 + 2
  semantic_engine.py  ← Classificação por domínio
  schema_discovery.py ← Orquestrador principal
  registry.py     ← DataSourceRegistry (JSON file)
  profiler.py     ← Estatísticas de colunas
  quality_scorer.py   ← Score de qualidade 0-100

nl2sql/           ← Sprint 3
  engine.py       ← NL → SQL via LLM
  validator.py    ← Segurança SQL
  executor.py     ← DuckDB in-memory
  router.py       ← Decisão NL2SQL/RAG/HYBRID/DIRECT

rag/              ← Sprint 4
  vector_store.py ← FAISS per-source
  document_indexer.py
  hybrid_retriever.py

analyst/          ← Sprint 5
  kpi_generator.py
  anomaly_detector.py
  insight_engine.py

actions/          ← Sprint 6
  base.py, registry.py, planner.py
  builtin/        ← send_email, generate_report, create_alert

graph/            ← Sprint 7
  entity_extractor.py
  relation_builder.py
  knowledge_graph.py
  graph_store.py

core/
  llm_client.py   ← Abstração Anthropic/OpenAI

src/              ← CÓDIGO LEGADO (Streamlit + logística)
  advanced_llm.py ← 51KB de código legado, hardcoded para logística
  (20+ arquivos)  ← Streamlit, Google Sheets, predicção, etc.
```

### Frontend (`/frontend/src`)
```
pages/
  LoginPage.tsx         ← Login com demo creds
  ChatPage.tsx          ← Chat com histórico
  DataSourcesPage.tsx   ← Gerenciar fontes
  AnalyticsPage.tsx     ← AI Analyst dashboard
  AlertsPage.tsx        ← Alertas + ações
  GraphPage.tsx         ← Knowledge Graph (canvas)
  SettingsPage.tsx      ← Estático (hardcoded)

components/
  Sidebar.tsx, Header.tsx, Layout.tsx
  ChatMessage.tsx, ConversationList.tsx
  ProtectedRoute.tsx, QuickActions.tsx

services/api.ts         ← Axios + interceptor JWT + todas as funções
contexts/
  AuthContext.tsx, ChatContext.tsx, ThemeContext.tsx
```

### Infraestrutura
- **Docker**: INEXISTENTE (nenhum Dockerfile ou docker-compose.yml)
- **CI/CD**: INEXISTENTE
- **Monitoring**: INEXISTENTE
- **Testes**: 1 arquivo de teste em `/backend/tests/` (vazio/mínimo)
- **Logs**: Arquivo `api.log` em `/logs/` (logging básico)

---

## ESTADO DOS SERVIDORES

- **Backend**: FastAPI na porta 5000 (com `--reload`)
- **Frontend**: Vite dev server na porta 5173
- **Banco de dados**: Nenhum servidor necessário (JSON files)
- **Redis**: Referenciado no config mas não usado
- **OpenSearch**: Referenciado no config/Settings mas não conectado

# 02 — PROGRESSO DO ROADMAP
> Análise fase a fase com evidências de código.

---

## FASE 0 — Universal Semantic Engine
**Status: ✅ CONCLUÍDO (90%)**

### O que existe
- `catalog/semantic_engine.py` — `SemanticEngine` com `_DOMAIN_SIGNALS` para 10 domínios: FINANCIAL, HR, CRM, LOGISTICS, ECOMMERCE, MARKETING, SUPPORT, LEGAL, ERP, OPERATIONS
- Classificação por padrão de tokens: tabelas + colunas analisadas com regex + score normalizado
- Fallback LLM via `LLMClient` para casos de baixa confiança (< 0.2)
- `DataDomain` enum em `connectors/base.py` com 11 valores incluindo UNKNOWN
- Integração completa com `SchemaDiscovery` → aplicado automaticamente em `/connect`

### Evidências
```
catalog/semantic_engine.py:27  _DOMAIN_SIGNALS: 10 domínios definidos
catalog/semantic_engine.py:139 classify() → DomainClassification
catalog/schema_discovery.py:55 self.semantic_engine = SemanticEngine()
api/routers/datasources.py:174 report = _discovery.discover(source_id) → classifica
```

### Gap (10%)
- Sem testes unitários para validar a classificação
- Fallback LLM falha silenciosamente se ANTHROPIC_API_KEY esgotado (atual situação)

---

## FASE 1 — Universal Connectors
**Status: ✅ CONCLUÍDO (75%)**

### Implementado
| Conector | Arquivo | Status |
|---|---|---|
| CSV | `connectors/files/csv_connector.py` | ✅ Completo |
| Excel (XLSX/XLS) | `connectors/files/excel_connector.py` | ✅ Completo |
| JSON | `connectors/files/json_connector.py` | ✅ Completo |
| Parquet | `connectors/files/parquet_connector.py` | ✅ Completo |
| PDF/DOCX/TXT/XML | `connectors/files/document_connector.py` | ✅ Completo |
| PostgreSQL | `connectors/databases/postgres_connector.py` | ✅ Completo |
| MySQL | `connectors/databases/mysql_connector.py` | ✅ Completo |
| SQLite | `connectors/databases/sqlite_connector.py` | ✅ Completo |

### Parcial
| Conector | Status |
|---|---|
| MongoDB | Enum `MONGODB` declarado em `ConnectorType` mas **sem implementação** |
| SQL Server | Enum `SQLSERVER` declarado mas **sem implementação** |

### Não iniciado
| Conector | Status |
|---|---|
| Google Drive | `ConnectorType.GOOGLE_DRIVE` declarado, **sem implementação** |
| S3 | `ConnectorType.S3` declarado, **sem implementação** |
| OneDrive | `ConnectorType.ONEDRIVE` declarado, **sem implementação** |
| REST API | `ConnectorType.REST` declarado, **sem implementação** |
| GraphQL | `ConnectorType.GRAPHQL` declarado, **sem implementação** |

### Evidências
```
connectors/base.py:15-37  ConnectorType enum com 18 tipos declarados
connectors/__init__.py     Importa somente files + databases
connectors/files/__init__.py:351  5 conectores registrados
connectors/databases/__init__.py:214  3 conectores registrados
```

---

## FASE 2 — Metadata Catalog
**Status: ✅ CONCLUÍDO (85%)**

### O que existe
- `catalog/registry.py` — `DataSourceRegistry` (CRUD completo, persistência JSON, mascaramento de senhas)
- `catalog/schema_discovery.py` — Orquestrador: conector → discover → classify → profile → quality → registry
- `catalog/profiler.py` — `DataProfiler`: estatísticas por coluna (dtype, nulls, unique, percentis, top valores)
- `catalog/quality_scorer.py` — `DataQualityScorer`: score 0-100 com grade (A/B/C/D/F) + recomendações
- APIs expostas: `GET /profile`, `GET /quality`, `GET /catalog/summary`

### Gap (15%)
- Registry persiste em JSON (sem PostgreSQL conforme planejado)
- Sem versionamento de schema (alterações de coluna não rastreadas)
- Sem relacionamentos entre tabelas (foreign keys)
- Sem linhagem de dados (data lineage)
- `catalog/` tem 5 arquivos vs. catálogo enterprise-grade esperado

---

## FASE 3 — NL2SQL
**Status: ✅ CONCLUÍDO (80%)**

### O que existe
- `nl2sql/engine.py` — `NL2SQLEngine`: prompt engineering, schema context builder, JSON parsing
- `nl2sql/validator.py` — `SQLValidator`: bloqueia DDL/DML/injection, whitelist de tabelas, LIMIT automático
- `nl2sql/executor.py` — `SQLExecutor`: DuckDB para arquivos, connectors nativos para DBs
- `nl2sql/router.py` — `QueryRouter`: heurística keyword + LLM fallback para NL2SQL/RAG/HYBRID/DIRECT
- APIs: `POST /query` (universal), `POST /datasources/{id}/query` (direto)

### Gap (20%)
- **Multi-source join não implementado**: comentário no código: `"multi-source join is Sprint 4+"`
- Sem histórico de queries / cache de resultados
- Sem feedback loop (o usuário não pode corrigir SQL gerado)
- Sem explainability visual (plano de execução)
- Dialect "DuckDB" para arquivos funciona, mas dialect PostgreSQL/MySQL não testado end-to-end

---

## FASE 4 — Hybrid RAG
**Status: ✅ CONCLUÍDO (70%)**

### O que existe
- `rag/vector_store.py` — `VectorStore`: FAISS per-source, OpenAI embeddings ou TF-IDF fallback
- `rag/document_indexer.py` — Indexa documentos (PDF/DOCX/TXT) em chunks → VectorStore
- `rag/hybrid_retriever.py` — `HybridRetriever`: NL2SQL + vector search → síntese LLM
- Integração no `query.py` router com tipo HYBRID e RAG

### Gap (30%)
- **Busca híbrida (BM25 + vetorial) não implementada**: apenas vetorial FAISS ou TF-IDF separados
- **Sem Qdrant, Chroma ou pgvector** — apenas FAISS em disco
- `api/rag_service.py` é um serviço LEGADO com FAISS global (não por fonte) que ainda convive com o novo `rag/vector_store.py` — duplicação
- `backend/vector_index.faiss` (21MB) e `backend/documents.pkl` (6.9MB) são índices globais do sistema legado, ainda no repositório
- Sem reranking
- Sem cross-encoder

---

## FASE 5 — AI Data Analyst
**Status: ✅ CONCLUÍDO (75%)**

### O que existe
- `analyst/kpi_generator.py` — `KPIGenerator`: KPIs por domínio (financial, hr, crm, logistics, ecommerce, marketing) + genéricos
- `analyst/anomaly_detector.py` — `AnomalyDetector`: outliers, valores negativos/zero, alta taxa de nulos, risco de concentração, gaps temporais
- `analyst/insight_engine.py` — `InsightEngine`: orquestra KPI + anomalias, gera executive summary
- API: `POST /datasources/{id}/analyze`

### Gap (25%)
- **Executive summary sem LLM real**: gerada por string concatenation, não por síntese LLM
- Sem tendências temporais (trend detection)
- Sem comparação com períodos anteriores
- Sem alertas automáticos agendados (trigger proativo)
- Análise roda on-demand; sem job de background

---

## FASE 6 — Agent Actions
**Status: ✅ CONCLUÍDO (65%)**

### O que existe
- `actions/base.py` — `Action`, `ActionContext`, `ActionResult`, `ActionStatus`
- `actions/registry.py` — `ActionRegistry` singleton
- `actions/planner.py` — `ActionPlanner`: rule-based + LLM-assisted planning
- `actions/builtin/send_email.py` — Mock/log only (sem SMTP real)
- `actions/builtin/generate_report.py` — Gera JSON/Markdown/HTML em `../dados/reports/`
- `actions/builtin/create_alert.py` — Persiste JSONL em `../dados/alerts/alerts.jsonl`
- APIs: `POST /datasources/{id}/act`, `GET /datasources/alerts`, `GET /datasources/actions/catalog`

### Gap (35%)
- **Send Email é simulado**: não há SMTP/SendGrid/SES configurado
- **Sem integração com Jira** (mencionado no roadmap original)
- **Sem webhooks reais** (create_alert tem campo webhook mas não implementado)
- Sem scheduler/agendamento de ações recorrentes
- **Sem LangGraph**: planner é rule-based com fallback LLM simples (sem grafo de agentes)
- Sem aprovação humana (human-in-the-loop)

---

## FASE 7 — Knowledge Graph
**Status: ✅ CONCLUÍDO (70%)**

### O que existe
- `graph/entity_extractor.py` — Extrai entidades tipadas (CUSTOMER, PRODUCT, EMPLOYEE, LOCATION, etc.) por padrão de coluna
- `graph/relation_builder.py` — Infere relações por co-ocorrência com peso normalizado
- `graph/knowledge_graph.py` — NetworkX DiGraph com queries, centralidade, serialização JSON, output vis.js/D3-ready
- `graph/graph_store.py` — Build + persistência por source_id em `../dados/graphs/`
- APIs: `POST/GET /graph`, `/graph/search`, `/graph/entity/{id}`

### Gap (30%)
- **Sem camada semântica** (ontologia, embeddings de entidades)
- Extração de entidades baseada apenas em padrão de coluna — sem NLP/NER real
- Sem fusão de entidades entre fontes diferentes
- Sem grafo de conhecimento cross-source
- Sem persistência em grafo DB (Neo4j, Neptune, FalkorDB)
- Frontend `GraphPage.tsx` usa canvas HTML5 simples, não vis.js ou Cytoscape

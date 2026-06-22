# 03 — GAPS ENCONTRADOS
> Tudo que foi planejado mas não existe no código atual.

---

## 1. INFRAESTRUTURA (Crítico)

### Docker / Containerização
- **Nenhum Dockerfile** em qualquer nível do projeto
- **Nenhum docker-compose.yml**
- Resultado: deploy impossível sem configuração manual do ambiente
- Impacto: bloqueia SaaS, staging, produção

### PostgreSQL
- O `catalog/registry.py` tem comentário: *"Persists to JSON for now (Sprint 2 migrates to PostgreSQL)"*
- O `api/config.py` não tem `DATABASE_URL`
- Resultado: todo o estado do sistema (fontes, datasets) está em JSON file
- Impacto: sem concorrência, sem backup transacional, sem queries relacionais

### Redis / Cache
- `api/config.py` define `REDIS_URL = "redis://localhost:6379"` mas **nenhum código usa Redis**
- `settings.ENABLE_CACHE = True` mas cache não está implementado
- Resultado: sem cache de embeddings, sem rate limiting real

### OpenSearch
- Referenciado em `api/config.py` (`OPENSEARCH_URL`) mas **nunca conectado**
- Resultado: busca híbrida BM25+vetorial não existe

---

## 2. CONNECTORS NÃO IMPLEMENTADOS (Alto Impacto)

Declarados em `ConnectorType` mas sem código:

| Conector | Importância |
|---|---|
| MongoDB | Alta (NoSQL popular) |
| SQL Server | Alta (mercado enterprise) |
| Google Drive | Média |
| Amazon S3 | Alta |
| OneDrive | Média |
| REST API genérico | Alta |
| GraphQL | Baixa |

---

## 3. MULTI-TENANCY (Crítico para SaaS)

- `DataSourceRecord` tem campo `owner_id = "default"` — hardcoded
- `DataSourceRegistry.list()` aceita `owner_id` como filtro mas não é usado nas APIs
- Nenhum middleware de isolamento de tenant
- Sem espaço de trabalho por organização/usuário
- **Resultado**: todos os usuários veem todas as fontes — sistema single-tenant

---

## 4. AUTENTICAÇÃO E AUTORIZAÇÃO (Alto)

- `REQUIRE_AUTH = False` em `api/config.py` — **todas as APIs são públicas por padrão**
- `AuthMiddleware` em `middleware.py` tem comentário: `"TODO: Implementar validação real do token JWT"` — aceita qualquer string `"Bearer ..."`
- Sem RBAC (Role-Based Access Control)
- Sem permissões por fonte de dados
- Usuários salvos em JSON file (sem banco de dados)
- Secret key hardcoded: `"your-secret-key-change-in-production"`

---

## 5. AGENT FRAMEWORK (Médio)

### LangGraph — Não implementado
- Memory refere LangGraph como preferido para orquestração
- Zero arquivos ou imports de `langgraph` no projeto
- `ActionPlanner` é rule-based simples, não um grafo de agentes

### Agentes especializados — Não existem
- Sem AgentOrchestrator
- Sem agentes paralelos (pesquisa + análise + ação)
- Sem memória persistente de agentes

---

## 6. SEMANTIC LAYER (Alto)

- Planejado como diferencial arquitetural
- Zero implementação: sem `semantic_layer/` ou equivalente
- Sem aliases de negócio (ex: "receita" → campo `valor_total`)
- Sem métricas calculadas (ex: LTV = receita_total / n_pedidos)
- NL2SQL usa schema bruto sem tradução de termos de negócio

---

## 7. FRONTEND — FUNCIONALIDADES FALTANTES

### SettingsPage.tsx
- 100% estático/hardcoded: mostra "OpenRAG: Ativo", "OpenSearch: Online", "1.234 documentos"
- Nenhuma chamada de API real
- Não reflete estado real do sistema

### ChatPage.tsx
- Bug TypeScript confirmado: `setIsLoading` não existe em `ChatContextType`
- Chat não usa a nova arquitetura (NL2SQL + hybrid): ainda usa `/chat` legado
- `/chat` backend ainda aponta para `SimpleLLMService` + `RAGService` legado

### Ausências no frontend
- Sem visualização de qualidade de dados por fonte
- Sem tela de perfil de usuário / gerenciamento de conta
- Sem multi-tenant UI (workspace switching)
- Sem dashboard executivo consolidado
- Sem histórico de queries NL2SQL
- Sem tela de configuração de connectors avançados (MongoDB, S3, REST)

---

## 8. OBSERVABILIDADE (Crítico)

- Sem APM (Datadog, New Relic, Grafana)
- Sem métricas de uso (quantas queries, tokens gastos, latência p95)
- Sem alertas de sistema (disco cheio, API key expirada)
- Logging apenas em arquivo texto + console
- Sem estruturação de logs (sem JSON logging, sem trace IDs)
- Sem health check detalhado (verifica apenas se app está rodando)

---

## 9. ESCALABILIDADE (Crítico para produção)

- Sem workers assíncronos (Celery, ARQ, dramatiq)
- Jobs pesados (analyze, graph build) bloqueiam o processo FastAPI
- FAISS em disco: sem suporte a múltiplos processos simultâneos
- Registry JSON: race condition possível em alta concorrência
- Sem connection pooling configurado

---

## 10. SEGURANÇA (Alto)

- `api/config.py:35` — `SECRET_KEY: str = "your-secret-key-change-in-production"` hardcoded
- `api/middleware.py:61` — comentário `"TODO: Implementar validação real do token JWT"`
- `REQUIRE_AUTH = False` — todas as APIs sem auth
- Senhas de banco de dados armazenadas em plain text no `registry.json` (apenas mascaradas na resposta da API, não em disco)
- Sem HTTPS/TLS configurado
- Sem validação de input em campos de texto livre

---

## 11. TESTES (Crítico)

- `/backend/tests/` tem apenas 1 item (provavelmente vazio ou mínimo)
- Zero testes para: connectors, NL2SQL, RAG, analyst, graph, actions
- Sem fixtures, sem mocks de API externa
- Sem testes de integração
- Sem CI pipeline para executar testes

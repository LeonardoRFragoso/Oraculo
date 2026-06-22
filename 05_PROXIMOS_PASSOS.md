# 05 — PRÓXIMOS PASSOS
> Plano de execução priorizado. 10 tarefas ordenadas por impacto.

---

## MATRIZ DE PRIORIDADE

| # | Tarefa | Impacto | Complexidade | Dependências | Tempo Est. |
|---|---|---|---|---|---|
| 1 | Limpeza de código morto (`src/`) | Alto | Baixa | Nenhuma | 2h |
| 2 | Ativar autenticação real (REQUIRE_AUTH + JWT middleware) | Crítico | Média | Nenhuma | 4h |
| 3 | Docker + docker-compose | Crítico | Média | Nenhuma | 6h |
| 4 | Unificar sistemas RAG (chat → nova arquitetura) | Alto | Alta | #1 | 8h |
| 5 | PostgreSQL: migrar Registry + Users | Alto | Alta | #3 | 12h |
| 6 | Corrigir ChatPage (usar `/query` em vez de `/chat` legado) | Alto | Média | #4 | 6h |
| 7 | SettingsPage dinâmica + perfil de usuário | Médio | Média | #2 | 8h |
| 8 | Workers assíncronos para jobs pesados (analyze, graph build) | Alto | Alta | #3, #5 | 16h |
| 9 | Suite de testes mínima (connectors + NL2SQL + auth) | Alto | Alta | Nenhuma | 20h |
| 10 | Connectors faltantes: MongoDB + REST API + S3 | Médio | Alta | Nenhuma | 24h |

---

## DETALHE DAS TAREFAS

---

### TAREFA 1 — Limpeza de Código Morto
**Impacto**: Eliminar 22 arquivos / ~200KB de ruído. Clareza arquitetural imediata.  
**Complexidade**: Baixa — nenhum arquivo em `src/` é importado pela nova arquitetura.  
**Ações**:
1. Criar diretório `legacy/` na raiz
2. Mover `backend/src/` → `legacy/src/`
3. Mover `backend/vector_index.faiss`, `backend/documents.pkl` → `legacy/`
4. Remover `.streamlit/`, `perguntas.txt`, `analise/` (ou mover para docs)
5. Manter apenas 1 `requirements.txt` (consolidar ultra-minimal como base)

---

### TAREFA 2 — Autenticação Real
**Impacto**: Segurança básica de produção.  
**Complexidade**: Média.  
**Ações**:
1. `api/config.py`: mudar `REQUIRE_AUTH = True`
2. `api/middleware.py`: implementar validação JWT real usando `auth_service.decode_token()`
3. Adicionar `/api/auth/login` e `/api/auth/register` à lista de exclusão do middleware
4. Gerar `SECRET_KEY` aleatória e documentar no `.env.example`
5. Criptografar senhas de conexão no registry (usar `encryption.key` que já existe)

---

### TAREFA 3 — Docker
**Impacto**: Deploy, staging, onboarding de colaboradores.  
**Complexidade**: Média.  
**Ações**:
```
Dockerfile.backend  — Python 3.11, venv, uvicorn
Dockerfile.frontend — Node 20, npm build, nginx
docker-compose.yml  — backend + frontend + postgres + redis
.env.docker.example — vars de ambiente para containers
```

---

### TAREFA 4 — Unificar RAG
**Impacto**: Consistência de resultados, eliminar duplicação.  
**Complexidade**: Alta.  
**Ações**:
1. Reescrever `api/routers/chat.py` para usar `HybridRetriever` + `QueryRouter` (já existentes)
2. Remover `api/rag_service.py` (legado)
3. Atualizar `api/routers/files.py` para indexar uploads no `VectorStore` por source_id
4. Deletar `api/llm_service.py` legado (substituído por `core/llm_client.py`)

---

### TAREFA 5 — PostgreSQL
**Impacto**: Concorrência, backup, produção.  
**Complexidade**: Alta.  
**Ações**:
1. Adicionar `DATABASE_URL` em config
2. Criar models SQLAlchemy para `DataSourceRecord` e `User`
3. Migrar `DataSourceRegistry._load/_save` para SQLAlchemy session
4. Migrar `AuthService.users` para PostgreSQL
5. Criar alembic migrations

---

### TAREFA 6 — ChatPage Funcional
**Impacto**: Principal interface do usuário usará a arquitetura correta.  
**Complexidade**: Média.  
**Ações**:
1. Corrigir bug TypeScript `setIsLoading` em `ChatContext.tsx`
2. Reescrever `ChatPage.tsx` para chamar `POST /api/query` (em vez de `/chat`)
3. Mostrar SQL gerado e fontes usadas na resposta
4. Manter `/chat` como fallback para conversação sem dados

---

### TAREFA 7 — SettingsPage Dinâmica
**Impacto**: Operabilidade — usuário vê estado real do sistema.  
**Complexidade**: Média.  
**Ações**:
1. Expandir `GET /api/health` para retornar status de LLM, vector store, connectors disponíveis
2. Reescrever `SettingsPage.tsx` para consumir `/health` e `/auth/me`
3. Adicionar tela de troca de senha
4. Mostrar API key status (configurada/não configurada)

---

### TAREFA 8 — Workers Assíncronos
**Impacto**: Performance e escalabilidade para fontes grandes.  
**Complexidade**: Alta.  
**Ações**:
1. Instalar ARQ (async Redis queue) ou Celery
2. Mover `analyze`, `build_graph`, `connect/discovery` para background tasks
3. Endpoints retornam `task_id` imediatamente
4. Novo endpoint `GET /tasks/{task_id}` retorna status
5. Frontend mostra loading state real

---

### TAREFA 9 — Suite de Testes
**Impacto**: Confiança para refatorar, detectar regressões.  
**Complexidade**: Alta.  
**Ações**:
```
tests/
  test_connectors/     — CSV, Excel, PostgreSQL mock
  test_nl2sql/         — validator, executor DuckDB
  test_auth/           — login, JWT, REQUIRE_AUTH
  test_catalog/        — discovery, semantic engine
  test_integration/    — upload → connect → analyze
```

---

### TAREFA 10 — Connectors MongoDB + REST + S3
**Impacto**: Alcance de mercado enterprise.  
**Complexidade**: Alta.  
**Ações**:
1. `connectors/databases/mongodb_connector.py` — pymongo, discover collections
2. `connectors/cloud/rest_connector.py` — requests, autenticação Bearer/Basic, paginação
3. `connectors/cloud/s3_connector.py` — boto3, list objects, leitura CSV/Parquet
4. Registrar na factory de `SchemaDiscovery._build_connector()`

---

## CAMINHO CRÍTICO PARA PRODUÇÃO

```
Semana 1: Tarefas 1 + 2 + 3  (limpeza + segurança + docker)
Semana 2: Tarefas 4 + 6       (unificar RAG + chat funcional)  
Semana 3: Tarefas 5 + 7       (banco de dados + settings)
Semana 4: Tarefa 8            (workers)
Semana 5-6: Tarefas 9 + 10   (testes + connectors)
```

**Versão mínima implantável (MVP de Produção)**: Tarefas 1+2+3+4+6 → ~26h de desenvolvimento.

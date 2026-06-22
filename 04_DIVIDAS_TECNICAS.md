# 04 — DÍVIDAS TÉCNICAS
> Problemas encontrados no código existente. Arquivos específicos citados.

---

## 🔴 CRÍTICO

### 1. Código Morto — `backend/src/` (22 arquivos, ~200KB)
**Arquivo(s)**: `/backend/src/advanced_llm.py` (51KB), `/backend/src/api_server.py`, `/backend/src/data_ingestion.py`, `/backend/src/dashboard.py`, `/backend/src/google_sheets_integration.py`, `/backend/src/universal_cloud_integration.py`, etc.

**Problema**: Todo o diretório `src/` é o sistema legado Streamlit especializado em logística/comércio. Contém:
- Hardcoded para análise de "importação, exportação e cabotagem"
- Streamlit imports
- AdvancedLLMManager com 936 linhas misturando lógica de negócio logístico
- Google Sheets, sync_manager, budget_manager, predictive_analytics
- Nenhum arquivo em `src/` é importado pela nova arquitetura FastAPI

**Risco**: Confusão sobre qual é a arquitetura real. Nomes como `auth.py` em `src/` e `api/auth_service.py` conflitam.

**Ação**: Mover para `legacy/` ou deletar.

---

### 2. Duplo Sistema RAG — Inconsistência Arquitetural
**Arquivo(s)**: `/backend/api/rag_service.py` (legado, FAISS global) vs `/backend/rag/vector_store.py` (novo, per-source)

**Problema**:
- `api/rag_service.py` usa FAISS global com `vector_index.faiss` (21MB, na raiz do backend)
- `rag/vector_store.py` usa FAISS per-source em `../dados/vector_store/`
- O `api/routers/chat.py` usa o LEGADO (`from ..rag_service import RAGService`)
- O `api/routers/query.py` usa o NOVO (`from rag.hybrid_retriever import HybridRetriever`)
- Resultado: `/chat` e `/query` usam sistemas RAG completamente diferentes

**Risco**: Inconsistência de resultados, dados duplicados, manutenção dobrada.

---

### 3. AuthMiddleware Falso
**Arquivo**: `/backend/api/middleware.py:42-69`

```python
# TODO: Implementar validação real do token JWT
# Por enquanto, aceita qualquer token que comece com "Bearer "
if not auth_header.startswith("Bearer "):
    raise HTTPException(...)
return await call_next(request)  # Nunca valida o token de verdade
```

**Problema**: Mesmo com `REQUIRE_AUTH = True`, qualquer token `"Bearer qualquer_coisa"` passa.
**Risco**: Falsa sensação de segurança.

---

### 4. `REQUIRE_AUTH = False` em Produção
**Arquivo**: `/backend/api/config.py:34`

Todas as APIs estão públicas por padrão. Uma instância acessível externamente expõe:
- Dados de usuários
- Arquivos carregados
- Resultados de análises

---

### 5. Secret Key Hardcoded
**Arquivo**: `/backend/api/config.py:35`
```python
SECRET_KEY: str = "your-secret-key-change-in-production"
```
Se `.env` não sobrescrever, JWTs podem ser forjados por qualquer pessoa que conheça o default.

---

## 🟠 ALTO

### 6. Artefatos FAISS Binários no Repositório
**Arquivos**: 
- `/backend/vector_index.faiss` (21MB)
- `/backend/documents.pkl` (6.9MB)

Arquivos binários grandes commitados. Crescerão indefinidamente conforme documentos são adicionados.

---

### 7. Senhas em Plain Text no Registry
**Arquivo**: `/backend/catalog/registry.py:27`
```python
config: Dict[str, Any]  # connection params (passwords should be encrypted in prod)
```

A senha do PostgreSQL é salva em plain text em `../dados/catalog/registry.json`. O comentário reconhece o problema mas não resolve.

---

### 8. Singletons Não Sincronizados
**Arquivo**: `/backend/api/routers/datasources.py:33-34` e `/backend/api/routers/query.py:33`

Duas instâncias de `DataSourceRegistry` criadas em módulos diferentes. Embora `_load()` releia o JSON a cada operação, isso é caro e pode gerar race conditions.

---

### 9. Logs de Debug Excessivos no Chat
**Arquivo**: `/backend/api/routers/chat.py:55-73`

```python
logger.info(f"📊 RAG Stats: {stats}")
logger.info(f"✓ Usando RAG: {stats['total_documents']} documentos disponíveis")
logger.info(f"📝 Query: {request.query}")
# ... 8+ linhas de log por request
```

Em produção, cada mensagem de chat gera 10+ linhas de log informativo. Sem nível de log configurável por rota.

---

### 10. Análise Pesada Bloqueante
**Arquivo**: `/backend/api/routers/datasources.py:338-399`

`/act` executa:
1. `InsightEngine().analyze()` — processa todos os dataframes
2. `ActionPlanner.plan_only()` 
3. `ActionPlanner.plan_and_run()` — executa novamente o analyze interno

Isso significa que `analyze` é rodado **duas vezes** por chamada a `/act`. Para fontes grandes, bloqueia o event loop FastAPI.

---

## 🟡 MÉDIO

### 11. SettingsPage 100% Hardcoded
**Arquivo**: `/frontend/src/pages/SettingsPage.tsx`

Mostra "OpenRAG: Ativo", "1.234 documentos", "Hoje, 03:00" — valores falsos hardcoded. Nenhuma chamada de API.

---

### 12. ChatContext com Bug TypeScript
**Arquivo**: `/frontend/src/contexts/ChatContext.tsx:50`
```
error TS2561: Object literal may only specify known properties,
but 'setIsLoading' does not exist in type 'ChatContextType'.
Did you mean to write 'setLoading'?
```

Chat funcionalmente comprometido — o erro impede compilação com `strict`.

---

### 13. Múltiplos requirements.txt (7 arquivos)
**Arquivos**: `requirements.txt`, `requirements-api.txt`, `requirements-api-minimal.txt`, `requirements-cpu-only.txt`, `requirements-minimal.txt`, `requirements-openrag.txt`, `requirements-server.txt`, `requirements-ultra-minimal.txt`

Qual deles usar? Nenhum README indica claramente qual é o correto para produção.

---

### 14. Versão Conflitante na API
**Arquivo**: `/backend/api/main.py`

```python
app = FastAPI(version="4.0.0", ...)  # linha 59
@app.get("/")
return {"version": "3.0.0", ...}    # linha 96
```

Duas versões diferentes declaradas no mesmo arquivo.

---

### 15. Frontend: Funções de API sem Tipagem Completa
**Arquivo**: `/frontend/src/services/api.ts`

Funções como `analyzeDataSource`, `buildGraph` retornam `Promise<any>`. Sem tipagem dos responses impede detecção de erros em compile-time.

---

### 16. `documents.pkl` na Raiz do Backend
**Arquivo**: `/backend/documents.pkl`

Arquivo pickle de 6.9MB com dados de usuário commitado no repositório. Problema de privacidade e segurança — pode conter dados sensíveis de sessões anteriores.

---

## 🟢 BAIXO

### 17. Comentários em Inglês Misturados com Português
Código novo usa inglês (connectors, catalog, nl2sql, rag, graph). Código legado usa português. Inconsistência dificulta onboarding.

### 18. `analise/` Diretório
**Caminho**: `/analise/` (8 items, provavelmente arquivos de análise de dados do projeto original). Não pertence ao repositório de código.

### 19. `.streamlit/` na Raiz
**Caminho**: `/.streamlit/` — configuração de Streamlit do projeto legado, não removida.

### 20. `perguntas.txt` na Raiz
**Arquivo**: `/perguntas.txt` — arquivo de texto de desenvolvimento pessoal commitado.

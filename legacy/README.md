# Legacy Code

Este diretório contém código do sistema original Oráculo (Streamlit + logística).
**Não é utilizado pela arquitetura atual (FastAPI + React).**

Mantido temporariamente para referência histórica.
Pode ser deletado com segurança quando não for mais necessário.

## Conteúdo

- `src/` — Sistema Streamlit original especializado em análise logística/comercial
  - `advanced_llm.py` — AdvancedLLMManager (OpenAI, hardcoded para logística)
  - `api_server.py`, `data_ingestion.py`, `dashboard.py` — servidor Flask legado
  - `google_sheets_integration.py`, `universal_cloud_integration.py` — integrações legacy
- `vector_index.faiss` — Índice FAISS global do sistema legado (21MB)
- `documents.pkl` — Documentos pickled do sistema legado (6.9MB)
- `.streamlit/` — Configuração Streamlit
- `perguntas.txt` — Arquivo de desenvolvimento

## Arquitetura Atual

Ver `/backend/` e `/frontend/` para a implementação atual.

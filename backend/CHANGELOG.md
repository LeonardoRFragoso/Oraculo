# 📝 Changelog - Backend Oráculo

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

---

## [3.0.0] - 2024-03-12

### 🚀 Adicionado
- **API FastAPI completa** substituindo Streamlit
  - Endpoints REST para chat, upload, analytics
  - Documentação automática (Swagger/ReDoc)
  - Validação com Pydantic
  - Middlewares (CORS, Auth, Logging)
  - Injeção de dependências
  
- **Estrutura modular da API**
  - `api/main.py` - Aplicação principal
  - `api/config.py` - Configurações
  - `api/models.py` - Modelos de dados
  - `api/routers/` - Routers organizados
  - `api/middleware.py` - Middlewares customizados
  
- **Documentação completa**
  - `API_README.md` - Guia da API
  - `INSTALL_API.md` - Guia de instalação
  - `CHANGELOG.md` - Este arquivo
  
- **Scripts de execução**
  - `run_api.py` - Iniciar API facilmente

### 🗑️ Removido
- **Arquivos Streamlit legados**
  - `gptracker.py` - App Streamlit antigo
  - `oraculo.py` - App Streamlit novo
  - `setup.bat` - Setup Windows
  - `start_gptracker.bat` - Iniciar Windows
  - `start_simple.bat` - Iniciar simples
  - `install-server.sh` - Instalação servidor

### 🔧 Modificado
- **README.md** - Atualizado para focar na API
- **requirements-api.txt** - Corrigido (removido openrag inexistente)
- Estrutura de diretórios reorganizada

### 🐛 Corrigido
- Erro de instalação com `openrag` (pacote não existe no PyPI)
- Referências a pacotes inexistentes em requirements

---

## [2.0.0] - 2024-03-12

### 🚀 Adicionado
- Integração com OpenRAG
- Suporte a OpenSearch, Langflow, Docling
- Sistema de cache com Redis
- Workflows Langflow

### 🔧 Modificado
- Migração de FAISS para OpenSearch
- Atualização de dependências

---

## [1.0.0] - 2024-01-XX

### 🚀 Inicial
- Sistema GPTRACKER com Streamlit
- Integração com OpenAI GPT-4
- FAISS para vector store
- Análise de dados com Pandas
- Dashboard com Plotly

---

## Tipos de Mudanças

- 🚀 **Adicionado** - Novas funcionalidades
- 🔧 **Modificado** - Mudanças em funcionalidades existentes
- 🗑️ **Removido** - Funcionalidades removidas
- 🐛 **Corrigido** - Correções de bugs
- 🔒 **Segurança** - Correções de segurança
- 📝 **Documentação** - Mudanças na documentação
- ⚡ **Performance** - Melhorias de performance

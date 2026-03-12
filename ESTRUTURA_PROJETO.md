# 📁 Estrutura do Projeto Oráculo

Documentação da estrutura reorganizada do projeto após separação em backend/frontend.

---

## 🏗️ Estrutura Completa

```
Oraculo/
├── backend/                        # 🐍 Backend Python
│   ├── src/                       # Código fonte principal
│   │   ├── advanced_llm.py       # LLM Manager (legado)
│   │   ├── openrag_integration.py # OpenRAG Manager (novo)
│   │   ├── auth.py               # Sistema de autenticação
│   │   ├── config.py             # Configurações centralizadas
│   │   ├── data_ingestion.py     # Ingestão de dados
│   │   ├── export_manager.py     # Exportação de dados
│   │   └── context_builder.py    # Construção de contexto
│   │
│   ├── scripts/                   # Scripts de automação
│   │   ├── setup_openrag.sh      # Setup automático OpenRAG
│   │   ├── migrate_to_openrag.py # Migração de dados
│   │   └── validate_openrag.py   # Validação pós-migração
│   │
│   ├── tests/                     # Testes automatizados
│   │   └── test_openrag_integration.py
│   │
│   ├── gptracker.py              # App Streamlit (legado)
│   ├── oraculo.py                # App Streamlit (novo)
│   ├── README.md                 # Documentação do backend
│   ├── pytest.ini                # Configuração pytest
│   ├── requirements.txt          # Dependências básicas
│   ├── requirements-openrag.txt  # Dependências OpenRAG
│   ├── requirements-minimal.txt  # Dependências mínimas
│   ├── requirements-server.txt   # Dependências servidor
│   ├── requirements-cpu-only.txt # CPU only (sem GPU)
│   ├── documents.pkl             # Dados (legado)
│   ├── vector_index.faiss        # Índice FAISS (legado)
│   ├── encryption.key            # Chave de criptografia
│   ├── users.json                # Usuários
│   ├── setup.bat                 # Setup Windows
│   ├── start_gptracker.bat       # Iniciar Windows
│   ├── start_simple.bat          # Iniciar simples Windows
│   └── install-server.sh         # Instalação servidor
│
├── frontend/                      # ⚛️ Frontend React
│   ├── src/                      # Código React
│   │   ├── components/           # Componentes reutilizáveis
│   │   │   ├── Layout.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── TypingIndicator.tsx
│   │   │   ├── WelcomeMessage.tsx
│   │   │   └── QuickActions.tsx
│   │   │
│   │   ├── pages/                # Páginas da aplicação
│   │   │   ├── ChatPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   │
│   │   ├── contexts/             # Context providers
│   │   │   ├── ThemeContext.tsx
│   │   │   └── ChatContext.tsx
│   │   │
│   │   ├── services/             # Serviços e API
│   │   │   └── api.ts
│   │   │
│   │   ├── types/                # TypeScript types
│   │   │   └── index.ts
│   │   │
│   │   ├── App.tsx               # App principal
│   │   ├── main.tsx              # Entry point
│   │   └── index.css             # Estilos globais
│   │
│   ├── public/                    # Assets públicos
│   ├── package.json               # Dependências Node
│   ├── vite.config.ts            # Configuração Vite
│   ├── tsconfig.json             # Configuração TypeScript
│   ├── tailwind.config.js        # Configuração Tailwind
│   ├── postcss.config.js         # Configuração PostCSS
│   ├── index.html                # HTML template
│   ├── .env.example              # Exemplo de variáveis
│   ├── .gitignore                # Git ignore
│   └── README.md                 # Documentação frontend
│
├── docs/                          # 📚 Documentação
│   ├── QUICKSTART_OPENRAG.md     # Início rápido OpenRAG
│   ├── MIGRATION_PLAN.md         # Plano de migração
│   ├── IMPLEMENTATION_SUMMARY.md # Resumo da implementação
│   ├── ERRORS_IDENTIFIED.md      # Erros identificados
│   ├── RESUMO_FINAL.md           # Resumo final
│   ├── INDEX.md                  # Índice de navegação
│   ├── ORACULO_BRANDING.md       # Guia de branding
│   ├── RENOMEACAO.md             # Plano de renomeação
│   ├── TRANSFORMACAO_ORACULO.md  # Transformação completa
│   ├── CHANGELOG_OPENRAG.md      # Changelog OpenRAG
│   ├── AJUSTES_IMPLEMENTADOS.md  # Ajustes implementados
│   ├── GUIA_INSTALACAO.md        # Guia de instalação
│   ├── MANUAL_USUARIO.md         # Manual do usuário
│   └── README_OPENRAG.md         # README OpenRAG
│
├── langflow_workflows/            # 🔄 Workflows Langflow
│   ├── data_ingestion.json       # Pipeline de ingestão
│   ├── rag_chat.json             # Chat com RAG
│   └── README.md                 # Documentação workflows
│
├── dados/                         # 📊 Dados
│   ├── processed/                # Dados processados
│   └── raw/                      # Dados brutos
│
├── analise/                       # 📈 Análises
├── logs/                          # 📝 Logs
├── .streamlit/                    # ⚙️ Config Streamlit
│
├── docker-compose.openrag.yml     # 🐳 Docker Compose OpenRAG
├── Dockerfile.api                 # 🐳 Dockerfile API
├── .dockerignore                  # Docker ignore
├── Makefile                       # 🛠️ Comandos úteis
├── .env                          # Variáveis de ambiente (não versionar)
├── .env.example                  # Exemplo de variáveis
├── .env.openrag.example          # Exemplo OpenRAG
├── .gitignore                    # Git ignore
├── README.md                     # 📖 README principal
├── README_ORACULO.md             # README Oráculo
├── ESTRUTURA_PROJETO.md          # 📁 Este arquivo
├── perguntas.txt                 # Perguntas frequentes
└── test_improved_responses.py    # Testes de resposta
```

---

## 🎯 Separação de Responsabilidades

### **Backend (`backend/`)**
- ✅ Lógica de negócio
- ✅ Integração com OpenAI
- ✅ Integração com OpenRAG
- ✅ Processamento de dados
- ✅ API REST (se implementado)
- ✅ Streamlit apps

### **Frontend (`frontend/`)**
- ✅ Interface do usuário
- ✅ Componentes React
- ✅ Gerenciamento de estado
- ✅ Integração com API
- ✅ Temas e estilos

### **Docs (`docs/`)**
- ✅ Toda documentação
- ✅ Guias e manuais
- ✅ Planos e resumos
- ✅ Changelogs

### **Workflows (`langflow_workflows/`)**
- ✅ Workflows Langflow
- ✅ Pipelines de dados
- ✅ Configurações RAG

---

## 🚀 Como Executar

### **Backend**

```bash
# Navegar para backend
cd backend

# Instalar dependências
pip install -r requirements-openrag.txt

# Executar Streamlit (Oráculo)
streamlit run oraculo.py

# Ou legado
streamlit run gptracker.py
```

### **Frontend**

```bash
# Navegar para frontend
cd frontend

# Instalar dependências
npm install

# Executar em desenvolvimento
npm run dev

# Build para produção
npm run build
```

### **OpenRAG (Docker)**

```bash
# Na raiz do projeto
docker-compose -f docker-compose.openrag.yml up -d
```

---

## 📝 Imports Atualizados

### **Antes (raiz do projeto)**
```python
from src.openrag_integration import HybridLLMManager
from src.auth import auth_manager
from src.config import OPENRAG_CONFIG
```

### **Depois (dentro de backend/)**
```python
# Mesmo import, pois estamos dentro de backend/
from src.openrag_integration import HybridLLMManager
from src.auth import auth_manager
from src.config import OPENRAG_CONFIG
```

**Nota:** Os imports **não precisam ser alterados** porque os arquivos Python foram movidos juntos mantendo a estrutura relativa.

---

## 🔄 Migração Realizada

### **Movidos para `backend/`**
- ✅ `src/` → `backend/src/`
- ✅ `scripts/` → `backend/scripts/`
- ✅ `tests/` → `backend/tests/`
- ✅ `gptracker.py` → `backend/gptracker.py`
- ✅ `oraculo.py` → `backend/oraculo.py`
- ✅ `requirements*.txt` → `backend/requirements*.txt`
- ✅ `pytest.ini` → `backend/pytest.ini`
- ✅ `*.bat`, `*.sh` → `backend/`
- ✅ `*.pkl`, `*.faiss`, `*.key`, `*.json` → `backend/`

### **Movidos para `docs/`**
- ✅ Todos os arquivos `.md` de documentação
- ✅ Guias, manuais, planos
- ✅ Changelogs e resumos

### **Permaneceram na raiz**
- ✅ `README.md` (principal)
- ✅ `docker-compose.openrag.yml`
- ✅ `Dockerfile.api`
- ✅ `.dockerignore`
- ✅ `Makefile`
- ✅ `.env*`
- ✅ `.gitignore`
- ✅ Diretórios: `dados/`, `analise/`, `logs/`, `.streamlit/`

---

## 🎨 Benefícios da Nova Estrutura

### **Organização**
- ✅ Separação clara de responsabilidades
- ✅ Código backend isolado
- ✅ Frontend independente
- ✅ Documentação centralizada

### **Desenvolvimento**
- ✅ Desenvolvimento paralelo backend/frontend
- ✅ Deploy independente
- ✅ Testes isolados
- ✅ Manutenção facilitada

### **Escalabilidade**
- ✅ Backend pode servir múltiplos frontends
- ✅ Frontend pode consumir múltiplos backends
- ✅ Microserviços no futuro
- ✅ CI/CD simplificado

---

## 🔧 Próximos Passos

1. **Testar Backend**
   ```bash
   cd backend
   streamlit run oraculo.py
   ```

2. **Testar Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Criar API REST** (opcional)
   - Implementar FastAPI no backend
   - Conectar frontend à API

4. **Atualizar CI/CD**
   - Configurar pipelines separados
   - Deploy automático

---

**Data:** 12 de Março de 2025  
**Versão:** 3.0.0 - Oráculo Edition  
**Status:** ✅ Reorganização Completa

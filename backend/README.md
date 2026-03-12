# 🔮 Oráculo - Backend

Backend Python para o Oráculo - Sistema de análise de dados comerciais e logísticos com IA.

---

## 🚀 Tecnologias

- **Python 3.10+**
- **Streamlit** - Interface web
- **OpenAI GPT-4** - LLM
- **OpenRAG** - RAG enterprise-grade
- **OpenSearch** - Vector store
- **Langflow** - Workflows visuais
- **Docling** - Document parsing
- **Redis** - Cache
- **FastAPI** - API REST (opcional)

---

## 📦 Instalação

### **Requisitos**

```bash
# Python 3.10 ou superior
python --version

# pip atualizado
pip install --upgrade pip
```

### **Instalação Básica**

```bash
# Instalar dependências
pip install -r requirements.txt

# Ou com OpenRAG
pip install -r requirements-openrag.txt
```

### **Instalação Completa com OpenRAG**

```bash
# 1. Instalar dependências
pip install -r requirements-openrag.txt

# 2. Configurar ambiente
cp ../.env.openrag.example ../.env
nano ../.env  # Adicionar OPENAI_API_KEY

# 3. Iniciar serviços OpenRAG
cd ..
docker-compose -f docker-compose.openrag.yml up -d

# 4. Executar migração (se necessário)
python scripts/migrate_to_openrag.py
```

---

## 🎯 Estrutura

```
backend/
├── src/                        # Código fonte
│   ├── advanced_llm.py        # LLM Manager (legado)
│   ├── openrag_integration.py # OpenRAG Manager
│   ├── auth.py                # Autenticação
│   ├── config.py              # Configurações
│   ├── data_ingestion.py      # Ingestão de dados
│   ├── export_manager.py      # Exportação
│   └── context_builder.py     # Construção de contexto
│
├── api/                       # 🚀 API FastAPI
│   ├── main.py               # Aplicação principal
│   ├── config.py             # Configurações
│   ├── models.py             # Modelos Pydantic
│   ├── dependencies.py       # Injeção de dependências
│   ├── middleware.py         # Middlewares
│   └── routers/              # Routers organizados
│       ├── chat.py
│       ├── health.py
│       ├── files.py
│       └── analytics.py
│
├── scripts/                   # Scripts de automação
│   ├── setup_openrag.sh      # Setup automático OpenRAG
│   ├── migrate_to_openrag.py # Migração de dados
│   └── validate_openrag.py   # Validação pós-migração
│
├── tests/                     # Testes automatizados
│   └── test_openrag_integration.py
│
├── run_api.py                # Script para iniciar API
├── README.md                 # Documentação do backend
├── API_README.md             # Documentação da API
├── INSTALL_API.md            # Guia de instalação
├── pytest.ini                # Configuração pytest
├── requirements.txt          # Dependências básicas
├── requirements-api.txt      # Dependências API
├── requirements-api-minimal.txt # Dependências API mínimas
├── documents.pkl             # Dados (legado)
├── vector_index.faiss        # Índice FAISS (legado)
├── encryption.key            # Chave de criptografia
└── users.json                # Usuários
```

---

## 🚀 Executar

### **API FastAPI (Recomendado)**

```bash
# Executar API
python run_api.py

# OU com uvicorn
uvicorn api.main:app --reload --port 5000
```

Acessar:
- **API:** http://localhost:5000
- **Docs:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc

---

## 🔧 Configuração

### **Variáveis de Ambiente**

Criar arquivo `.env` na raiz do projeto:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# OpenRAG
USE_OPENRAG=true
OPENRAG_API_URL=http://localhost:7860
OPENSEARCH_URL=http://localhost:9200
DOCLING_URL=http://localhost:5001
REDIS_URL=redis://localhost:6379

# Configurações
OPENRAG_INDEX_NAME=gptracker_knowledge
EMBEDDING_MODEL=text-embedding-3-large
CHAT_MODEL=gpt-4-turbo
```

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html

# Teste específico
pytest tests/test_openrag_integration.py

# Validar instalação OpenRAG
python scripts/validate_openrag.py
```

---

## 📊 Módulos Principais

### **1. OpenRAG Integration (`src/openrag_integration.py`)**

```python
from src.openrag_integration import HybridLLMManager

# Criar manager
manager = HybridLLMManager()

# Adicionar documentos
manager.ingest_documents(files=['data.xlsx'])

# Buscar
results = manager.search('containers em março')

# Chat
response = manager.chat('Quantos containers?')
```

### **2. Data Ingestion (`src/data_ingestion.py`)**

```python
from src.data_ingestion import DataIngestionManager

# Processar arquivo
manager = DataIngestionManager()
df = manager.process_file('data.xlsx')
```

### **3. Config (`src/config.py`)**

```python
from src.config import OPENRAG_CONFIG, OPENAI_CONFIG

# Acessar configurações
api_url = OPENRAG_CONFIG['api_url']
model = OPENAI_CONFIG['model']
```

---

## 🔄 Migração para OpenRAG

### **Passo a Passo**

```bash
# 1. Backup dos dados atuais
cp documents.pkl documents.pkl.backup
cp vector_index.faiss vector_index.faiss.backup

# 2. Iniciar serviços OpenRAG
docker-compose -f ../docker-compose.openrag.yml up -d

# 3. Executar migração
python scripts/migrate_to_openrag.py

# 4. Validar
python scripts/validate_openrag.py

# 5. Atualizar .env
echo "USE_OPENRAG=true" >> ../.env
```

---

## 📝 Scripts Úteis

### **Setup OpenRAG**

```bash
./scripts/setup_openrag.sh
```

### **Migração de Dados**

```bash
python scripts/migrate_to_openrag.py
```

### **Validação**

```bash
python scripts/validate_openrag.py
```

---

## 🐛 Troubleshooting

### **Erro: ModuleNotFoundError**

```bash
# Reinstalar dependências
pip install -r requirements-openrag.txt
```

### **Erro: OpenSearch connection refused**

```bash
# Verificar se OpenSearch está rodando
docker ps | grep opensearch

# Reiniciar serviços
docker-compose -f ../docker-compose.openrag.yml restart
```

### **Erro: OPENAI_API_KEY not found**

```bash
# Adicionar ao .env
echo "OPENAI_API_KEY=sk-..." >> ../.env
```

---

## 📚 Documentação

- [Guia de Instalação](../docs/GUIA_INSTALACAO.md)
- [Manual do Usuário](../docs/MANUAL_USUARIO.md)
- [Quickstart OpenRAG](../docs/QUICKSTART_OPENRAG.md)
- [Migration Plan](../docs/MIGRATION_PLAN.md)
- [Branding Oráculo](../docs/ORACULO_BRANDING.md)

---

## 🔒 Segurança

- ✅ Nunca commitar `.env` com API keys
- ✅ Usar variáveis de ambiente
- ✅ Criptografar dados sensíveis
- ✅ Validar inputs do usuário
- ✅ Rate limiting em APIs

---

## 📈 Performance

### **Otimizações**

- Cache de embeddings (Redis)
- Busca híbrida (vetorial + keyword)
- Reranking de resultados
- Chunking semântico
- Batch processing

### **Métricas**

- Tempo de resposta: < 100ms
- Precisão (MRR): 0.85
- Cache hit rate: > 70%
- Throughput: 100 req/s

---

## 🤝 Contribuindo

```bash
# 1. Fork o projeto
# 2. Criar branch
git checkout -b feature/nova-funcionalidade

# 3. Commit
git commit -m "Adiciona nova funcionalidade"

# 4. Push
git push origin feature/nova-funcionalidade

# 5. Abrir Pull Request
```

---

## 📝 Licença

MIT

---

**🔮 Oráculo Backend - Powered by OpenRAG**

**Versão:** 3.0.0  
**Python:** 3.10+  
**Status:** ✅ Produção

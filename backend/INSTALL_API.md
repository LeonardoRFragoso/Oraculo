# 🚀 Instalação da API FastAPI

Guia rápido para instalar e executar a API do Oráculo.

---

## ⚠️ **IMPORTANTE: Erro no requirements-openrag.txt**

Os pacotes `openrag` e `langflow-sdk` **não existem no PyPI**. Eles são referências a sistemas que devem ser instalados separadamente via Docker.

---

## 📦 **Instalação Rápida**

### **Opção 1: Dependências Mínimas (Recomendado)**

```bash
cd backend

# Instalar apenas FastAPI e dependências essenciais
pip install -r requirements-api-minimal.txt
```

Isso instala:
- ✅ FastAPI + Uvicorn
- ✅ Pydantic (validação)
- ✅ OpenAI
- ✅ Autenticação JWT
- ✅ HTTP clients

**Nota:** Pandas, sentence-transformers e faiss-cpu já foram instalados via `requirements.txt`.

---

### **Opção 2: Instalação Manual**

```bash
# FastAPI e servidor
pip install fastapi==0.109.0
pip install "uvicorn[standard]==0.27.0"

# Validação
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0

# HTTP e Auth
pip install httpx==0.26.0
pip install "python-jose[cryptography]==3.3.0"
pip install "passlib[bcrypt]==1.7.4"
pip install python-multipart==0.0.6
pip install email-validator==2.1.0

# Utilitários
pip install python-dotenv==1.0.0
pip install openai
```

---

## 🚀 **Executar a API**

```bash
cd backend

# Executar com script
python run_api.py

# OU executar com uvicorn
uvicorn api.main:app --reload --port 5000
```

Acessar:
- **API:** http://localhost:5000
- **Docs:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc

---

## ✅ **Verificar Instalação**

```bash
# Testar health check
curl http://localhost:5000/api/health

# Deve retornar:
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "...",
  "openrag": false,
  "opensearch": false,
  "langflow": false,
  "redis": false,
  "overall": true
}
```

---

## 🐳 **OpenRAG (Opcional)**

Se quiser usar OpenRAG, você precisa:

### **1. Iniciar Serviços Docker**

```bash
# Na raiz do projeto
docker-compose -f docker-compose.openrag.yml up -d
```

Isso inicia:
- OpenSearch (porta 9200)
- Langflow (porta 7860)
- Docling (porta 5001)
- Redis (porta 6379)

### **2. Configurar .env**

```bash
USE_OPENRAG=true
OPENRAG_API_URL=http://localhost:7860
OPENSEARCH_URL=http://localhost:9200
DOCLING_URL=http://localhost:5001
REDIS_URL=redis://localhost:6379
```

### **3. Instalar Clientes Python**

```bash
# OpenSearch client
pip install opensearch-py>=2.0.0

# Redis client
pip install redis>=4.5.0
```

**Nota:** `openrag` e `langflow-sdk` são SDKs que não existem como pacotes Python. A integração é feita via HTTP/REST.

---

## 🔧 **Troubleshooting**

### **Erro: openrag not found**

```bash
# SOLUÇÃO: Use requirements-api-minimal.txt
pip install -r requirements-api-minimal.txt
```

O pacote `openrag` não existe no PyPI. OpenRAG é um conjunto de serviços Docker.

### **Erro: Port 5000 already in use**

```bash
# Matar processo
lsof -ti:5000 | xargs kill -9

# OU usar outra porta
uvicorn api.main:app --port 8000
```

### **Erro: Module 'api' not found**

```bash
# Executar do diretório backend/
cd backend
python run_api.py
```

---

## 📝 **Modo de Operação**

### **Sem OpenRAG (Padrão)**

```bash
# .env
USE_OPENRAG=false

# A API funciona com:
# - OpenAI GPT-4 direto
# - FAISS local (legado)
# - Sem necessidade de Docker
```

### **Com OpenRAG**

```bash
# .env
USE_OPENRAG=true

# Requer:
# - Docker Compose rodando
# - OpenSearch, Langflow, Redis
# - Configurações de URL
```

---

## 🎯 **Próximos Passos**

1. **Instalar dependências:**
   ```bash
   pip install -r requirements-api-minimal.txt
   ```

2. **Configurar .env:**
   ```bash
   cp ../.env.example ../.env
   # Adicionar OPENAI_API_KEY
   ```

3. **Executar API:**
   ```bash
   python run_api.py
   ```

4. **Testar:**
   ```bash
   curl http://localhost:5000/docs
   ```

---

## 📚 **Documentação**

- [API README](API_README.md) - Guia completo da API
- [Backend README](README.md) - Documentação do backend
- [Docs](../docs/) - Documentação geral

---

**✅ Instalação Simplificada e Funcional!**

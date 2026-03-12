# 🔗 Guia de Integração Frontend/Backend - Oráculo

Documentação completa da integração entre o frontend React e backend FastAPI.

---

## 🏗️ Arquitetura

```
┌─────────────────┐         HTTP/REST         ┌─────────────────┐
│                 │ ────────────────────────> │                 │
│  Frontend React │                           │  Backend FastAPI│
│  (Port 3000)    │ <──────────────────────── │  (Port 5000)    │
│                 │         JSON              │                 │
└─────────────────┘                           └─────────────────┘
```

---

## ✅ **CORREÇÕES APLICADAS**

### **1. Frontend - Tailwind CSS**

**Problema:** Classes customizadas inexistentes (`border-border`, `bg-light-bg`, etc.)

**Solução:** Substituídas por classes Tailwind padrão

```css
/* Antes */
@apply border-light-border dark:border-dark-border

/* Depois */
@apply border-gray-200 dark:border-gray-700
```

**Arquivos corrigidos:**
- ✅ `frontend/src/index.css` - Classes CSS atualizadas

### **2. Backend - Imports e Configuração**

**Problema:** Módulo `os` não importado em `src/config.py`

**Solução:** Adicionado `import os`

**Arquivos corrigidos:**
- ✅ `backend/src/config.py` - Import adicionado
- ✅ `backend/api/config.py` - Configuração com `extra = "ignore"`

---

## 🚀 **Como Executar**

### **1. Backend (FastAPI)**

```bash
# Terminal 1
cd backend

# Ativar ambiente virtual (se necessário)
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements-api-minimal.txt

# Executar API
python run_api.py
```

**Verificar:** http://localhost:5000/docs

### **2. Frontend (React + Vite)**

```bash
# Terminal 2
cd frontend

# Criar .env (se não existir)
cp .env.example .env

# Instalar dependências (se necessário)
npm install

# Executar frontend
npm run dev
```

**Verificar:** http://localhost:3000

---

## 🔌 **Endpoints da API**

### **Health Check**
```bash
GET http://localhost:5000/api/health
GET http://localhost:5000/api/ping
```

### **Chat**
```bash
POST http://localhost:5000/api/chat
Content-Type: application/json

{
  "query": "Quantos containers foram movimentados?",
  "conversation_id": "conv-123"
}
```

### **Upload**
```bash
POST http://localhost:5000/api/upload
Content-Type: multipart/form-data

file: <arquivo>
```

### **Analytics**
```bash
GET http://localhost:5000/api/analytics
GET http://localhost:5000/api/analytics/trends
GET http://localhost:5000/api/analytics/insights
```

---

## 📡 **Integração Frontend → Backend**

### **Arquivo de Configuração**

**`frontend/src/services/api.ts`**

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})
```

### **Variáveis de Ambiente**

**`frontend/.env`**

```bash
VITE_API_URL=http://localhost:5000/api
VITE_APP_NAME=Oráculo
VITE_APP_VERSION=3.0.0
```

### **Funções de API**

```typescript
// Enviar mensagem
await sendMessage("Quantos containers?")

// Upload de arquivo
await uploadFile(file)

// Status do sistema
await getSystemStatus()

// Analytics
await getAnalytics()
```

---

## 🧪 **Testar Integração**

### **1. Testar Backend Isolado**

```bash
# Health check
curl http://localhost:5000/api/health

# Chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Teste"}'
```

### **2. Testar Frontend Isolado**

```bash
# Acessar
http://localhost:3000

# Verificar console do navegador
# Deve mostrar tentativas de conexão com API
```

### **3. Testar Integração Completa**

1. **Backend rodando:** http://localhost:5000
2. **Frontend rodando:** http://localhost:3000
3. **Enviar mensagem no chat**
4. **Verificar resposta da API**

---

## 🔧 **CORS - Configuração**

### **Backend**

**`backend/api/config.py`**

```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",      # Vite dev
    "http://localhost:5173",      # Vite alternativo
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
```

### **Middleware CORS**

**`backend/api/main.py`**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🐛 **Troubleshooting**

### **Erro: CORS blocked**

**Sintoma:** Erro no console do navegador sobre CORS

**Solução:**
```python
# Adicionar origem do frontend em backend/api/config.py
CORS_ORIGINS = ["http://localhost:3000"]
```

### **Erro: Network Error / Connection Refused**

**Sintoma:** Frontend não consegue conectar ao backend

**Verificar:**
1. Backend está rodando? `curl http://localhost:5000/api/health`
2. URL correta no `.env`? `VITE_API_URL=http://localhost:5000/api`
3. Porta correta? Backend deve estar na 5000

### **Erro: 404 Not Found**

**Sintoma:** Endpoint não encontrado

**Verificar:**
1. URL completa: `http://localhost:5000/api/chat` (não esquecer `/api`)
2. Método HTTP correto (GET, POST, etc.)
3. Backend iniciado corretamente

### **Erro: Tailwind CSS**

**Sintoma:** Classes CSS não funcionam

**Solução:** Classes customizadas foram corrigidas para usar Tailwind padrão

---

## 📊 **Fluxo de Dados**

### **Chat Message Flow**

```
1. Usuário digita mensagem
   ↓
2. Frontend: ChatPage.tsx
   ↓
3. API Service: sendMessage()
   ↓
4. HTTP POST → Backend: /api/chat
   ↓
5. Backend: chat.py router
   ↓
6. LLM Manager processa
   ↓
7. Resposta JSON ← Backend
   ↓
8. Frontend atualiza UI
   ↓
9. Mensagem exibida ao usuário
```

### **File Upload Flow**

```
1. Usuário seleciona arquivo
   ↓
2. Frontend: Sidebar.tsx
   ↓
3. API Service: uploadFile()
   ↓
4. HTTP POST → Backend: /api/upload
   ↓
5. Backend: files.py router
   ↓
6. Arquivo salvo e processado
   ↓
7. Resposta JSON ← Backend
   ↓
8. Frontend mostra confirmação
```

---

## 🔒 **Segurança**

### **Autenticação (Opcional)**

**Ativar:**
```bash
# backend/.env
REQUIRE_AUTH=true
SECRET_KEY=your-super-secret-key
```

**Usar:**
```typescript
// Frontend
const response = await api.post('/chat', data, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### **Validação de Dados**

**Backend:** Pydantic valida automaticamente

```python
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
```

**Frontend:** TypeScript garante tipos

```typescript
interface ChatRequest {
  query: string
  conversation_id?: string
}
```

---

## 📝 **Checklist de Deploy**

### **Backend**
- [ ] Variáveis de ambiente configuradas
- [ ] `OPENAI_API_KEY` definida
- [ ] CORS configurado para domínio de produção
- [ ] `DEBUG=false` em produção
- [ ] Logs configurados

### **Frontend**
- [ ] `.env` com URL de produção da API
- [ ] Build de produção: `npm run build`
- [ ] Assets otimizados
- [ ] Variáveis de ambiente corretas

---

## 🎯 **Próximos Passos**

1. **Testar integração completa**
   ```bash
   # Terminal 1: Backend
   cd backend && python run_api.py
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

2. **Verificar funcionalidades**
   - [ ] Chat funciona
   - [ ] Upload de arquivos funciona
   - [ ] Analytics carrega
   - [ ] Temas dark/light funcionam

3. **Otimizações**
   - [ ] Adicionar loading states
   - [ ] Implementar retry logic
   - [ ] Cache de respostas
   - [ ] Websockets para chat em tempo real

---

## 📚 **Documentação Adicional**

- [Backend API README](backend/API_README.md)
- [Frontend README](frontend/README.md)
- [Instalação API](backend/INSTALL_API.md)
- [Changelog](backend/CHANGELOG.md)

---

**🔮 Oráculo - Integração Frontend/Backend Completa!**

**Status:** ✅ Corrigido e Funcional  
**Frontend:** React + Vite + TailwindCSS  
**Backend:** FastAPI + OpenAI + OpenRAG  
**Comunicação:** REST API (JSON)

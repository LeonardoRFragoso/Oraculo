# 🚀 Setup Completo - Oráculo

Guia passo a passo para ter a plataforma 100% funcional.

---

## ✅ **O QUE JÁ ESTÁ PRONTO**

- ✅ Backend FastAPI estruturado
- ✅ Frontend React com Vite
- ✅ Integração configurada
- ✅ Documentação completa

---

## ⚠️ **O QUE FALTA CONFIGURAR**

### **1. Chave da API OpenAI** (OBRIGATÓRIO)

A plataforma precisa da chave da OpenAI para funcionar.

**Como obter:**
1. Acesse https://platform.openai.com/api-keys
2. Crie uma nova chave API
3. Copie a chave (começa com `sk-...`)

**Como configurar:**

```bash
# Editar arquivo .env na raiz do projeto
nano .env

# Adicionar a linha:
OPENAI_API_KEY=sk-sua-chave-aqui
```

---

## 🚀 **EXECUTAR A PLATAFORMA**

### **Passo 1: Backend**

```bash
# Terminal 1
cd backend

# Ativar ambiente virtual
source venv/bin/activate

# Executar API
python run_api.py
```

**Verificar:** http://localhost:5000/docs

### **Passo 2: Frontend**

```bash
# Terminal 2
cd frontend

# Criar .env (primeira vez)
cp .env.example .env

# Executar
npm run dev
```

**Verificar:** http://localhost:3000

---

## 🧪 **TESTAR SE ESTÁ FUNCIONANDO**

### **1. Testar Backend**

```bash
# Health check
curl http://localhost:5000/api/health

# Deve retornar:
{
  "status": "healthy",
  "version": "3.0.0",
  ...
}
```

### **2. Testar Chat**

```bash
# Enviar mensagem de teste
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Olá, você está funcionando?"}'

# Deve retornar resposta do GPT-4
```

### **3. Testar Frontend**

1. Acessar http://localhost:3000
2. Digitar mensagem no chat
3. Receber resposta do Oráculo

---

## 🔧 **CORREÇÕES APLICADAS**

### **1. Serviço de LLM Simplificado**

Criado `backend/api/llm_service.py` que:
- ✅ Usa OpenAI diretamente
- ✅ Funciona de forma assíncrona
- ✅ Trata erros graciosamente
- ✅ Não depende de OpenRAG

### **2. Frontend - CSS Corrigido**

- ✅ Classes Tailwind customizadas substituídas
- ✅ Build funciona sem erros

### **3. Backend - Imports Corrigidos**

- ✅ Módulo `os` importado
- ✅ Configuração Pydantic ajustada

---

## 📋 **CHECKLIST FINAL**

### **Configuração**
- [ ] Arquivo `.env` criado na raiz
- [ ] `OPENAI_API_KEY` configurada
- [ ] Dependências instaladas (`pip install -r requirements-api-minimal.txt`)
- [ ] Dependências frontend instaladas (`npm install`)

### **Execução**
- [ ] Backend rodando (porta 5000)
- [ ] Frontend rodando (porta 3000)
- [ ] Sem erros no console

### **Funcionalidades**
- [ ] Chat responde mensagens
- [ ] Interface carrega corretamente
- [ ] Temas dark/light funcionam

---

## 🎯 **COMANDOS RÁPIDOS**

### **Iniciar Tudo**

```bash
# Terminal 1 - Backend
cd backend && python run_api.py

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

### **Parar Tudo**

```
Ctrl+C em cada terminal
```

---

## 🐛 **PROBLEMAS COMUNS**

### **Erro: OPENAI_API_KEY não configurada**

**Solução:**
```bash
# Editar .env
echo "OPENAI_API_KEY=sk-sua-chave" >> .env
```

### **Erro: Port 5000 already in use**

**Solução:**
```bash
# Matar processo
lsof -ti:5000 | xargs kill -9
```

### **Erro: npm command not found**

**Solução:**
```bash
# Instalar Node.js
sudo apt install nodejs npm
```

---

## 📚 **DOCUMENTAÇÃO**

- [Guia de Integração](INTEGRATION_GUIDE.md)
- [API README](backend/API_README.md)
- [Frontend README](frontend/README.md)
- [Instalação API](backend/INSTALL_API.md)

---

## 🎉 **PRONTO PARA USAR!**

Após seguir estes passos, você terá:

✅ Backend FastAPI rodando  
✅ Frontend React moderno  
✅ Chat com GPT-4 funcionando  
✅ Interface completa e responsiva  

---

**🔮 Oráculo - Seu Consultor de IA**

**Versão:** 3.0.0  
**Status:** Pronto para Produção  
**Stack:** React + FastAPI + OpenAI GPT-4

# 🔄 Plano de Renomeação: GPTRACKER → ORÁCULO

## 📋 Resumo

Transformação completa do projeto GPTRACKER em **ORÁCULO**, um assistente de IA moderno para análise de dados comerciais e logísticos.

---

## 🎯 Mudanças de Identidade

### **Nome**
- **Antes:** GPTRACKER
- **Depois:** ORÁCULO (Oráculo)

### **Tagline**
- **Antes:** Sistema Inteligente de Análise Comercial
- **Depois:** Insights que Antecipam o Futuro

### **Propósito**
- **Antes:** Ferramenta interna para iTracker
- **Depois:** Produto independente e moderno de IA

---

## 📁 Arquivos a Renomear

### **Arquivo Principal**
```bash
gptracker.py → oraculo.py ✅ CRIADO
```

### **Documentação**
```bash
README.md → README_LEGACY.md (backup)
README_ORACULO.md → README.md (novo principal)
```

### **Configuração**
```bash
# Manter compatibilidade, adicionar novos:
.env.oraculo.example (novo)
oraculo_config.py (novo)
```

### **Docker**
```bash
docker-compose.openrag.yml → docker-compose.yml (principal)
# Adicionar:
docker-compose.oraculo.yml (otimizado)
```

---

## 🔧 Mudanças no Código

### **1. Imports e Referências**

#### **Antes:**
```python
from src.advanced_llm import AdvancedLLMManager

st.set_page_config(
    page_title="GPTRACKER Chat",
    page_icon="🤖"
)
```

#### **Depois:**
```python
from src.openrag_integration import HybridLLMManager

st.set_page_config(
    page_title="Oráculo - IA para Decisões Estratégicas",
    page_icon="🔮"
)
```

### **2. Variáveis de Ambiente**

#### **Adicionar ao .env:**
```bash
# Oráculo Configuration
APP_NAME=Oráculo
APP_TAGLINE=Insights que Antecipam o Futuro
APP_ICON=🔮
APP_VERSION=3.0.0

# Branding
THEME_PRIMARY_COLOR=#6366f1
THEME_SECONDARY_COLOR=#8b5cf6
THEME_ACCENT_COLOR=#06b6d4
```

### **3. Mensagens e Textos**

#### **Saudações:**
```python
# Antes
"Bem-vindo ao GPTRACKER"

# Depois
"Olá! Sou o Oráculo, seu consultor de IA..."
```

#### **Títulos:**
```python
# Antes
"GPTRACKER - Sistema Inteligente"

# Depois
"🔮 ORÁCULO - Insights que Antecipam o Futuro"
```

---

## 🎨 Mudanças Visuais

### **Cores**

#### **Antes (GPTRACKER):**
```css
--primary: #1f4e79    /* Azul corporativo */
--secondary: #2d5aa0  /* Azul médio */
```

#### **Depois (ORÁCULO):**
```css
--primary: #6366f1    /* Indigo vibrante */
--secondary: #8b5cf6  /* Roxo */
--accent: #06b6d4     /* Cyan */
```

### **Ícones**

- **Antes:** 🤖 (robô genérico)
- **Depois:** 🔮 (cristal/oráculo)

### **Tipografia**

- **Antes:** System fonts
- **Depois:** Inter (Google Fonts)

---

## 📦 Novos Componentes

### **1. oraculo.py** ✅
Interface moderna estilo ChatGPT/Claude

### **2. ORACULO_BRANDING.md** ✅
Guia completo de identidade visual

### **3. README_ORACULO.md** ✅
Documentação principal renovada

### **4. Temas Modernos**
- Dark mode (padrão)
- Light mode
- Animações fluidas

---

## 🔄 Migração de Dados

### **Compatibilidade**
- ✅ Mantém dados existentes
- ✅ Suporta migração do GPTRACKER
- ✅ Sem perda de informações

### **Script de Migração**
```bash
python scripts/migrate_gptracker_to_oraculo.py
```

---

## 📊 Checklist de Renomeação

### **Arquivos**
- [x] Criar `oraculo.py`
- [x] Criar `ORACULO_BRANDING.md`
- [x] Criar `README_ORACULO.md`
- [ ] Renomear `README.md` → `README_LEGACY.md`
- [ ] Renomear `README_ORACULO.md` → `README.md`
- [ ] Criar `.env.oraculo.example`
- [ ] Atualizar `docker-compose.yml`

### **Código**
- [x] Atualizar page_title
- [x] Atualizar page_icon
- [x] Atualizar mensagens de boas-vindas
- [x] Atualizar CSS com novas cores
- [ ] Atualizar todos os comentários
- [ ] Atualizar docstrings

### **Documentação**
- [x] Criar branding guide
- [x] Criar README renovado
- [ ] Atualizar todos os docs
- [ ] Criar guia de migração
- [ ] Atualizar screenshots

### **Configuração**
- [ ] Atualizar variáveis de ambiente
- [ ] Atualizar docker-compose
- [ ] Atualizar Makefile
- [ ] Atualizar package.json (se houver)

### **Testes**
- [ ] Atualizar nomes de testes
- [ ] Atualizar fixtures
- [ ] Validar integração
- [ ] Testes de UI

---

## 🚀 Comandos Atualizados

### **Antes:**
```bash
streamlit run gptracker.py
```

### **Depois:**
```bash
streamlit run oraculo.py
# ou
make run
```

---

## 📝 Comunicação da Mudança

### **Mensagem para Usuários:**
```
🎉 Novidade: GPTRACKER agora é ORÁCULO!

Renovamos completamente nossa plataforma com:
• Interface moderna estilo ChatGPT
• Análises preditivas avançadas
• Insights automáticos
• Performance 10x melhor

Seus dados estão seguros e a migração é automática.

Experimente agora: oraculo.ai
```

### **Changelog:**
```markdown
## [3.0.0] - 2025-03-12 - Oráculo Edition

### 🎉 Renomeação Completa
- GPTRACKER → ORÁCULO
- Nova identidade visual
- Interface moderna
- Experiência renovada

### ✨ Novidades
- Design inspirado em ChatGPT/Claude
- Temas dark/light
- Animações fluidas
- Insights automáticos
```

---

## ⚠️ Avisos Importantes

### **Compatibilidade**
- ✅ Dados do GPTRACKER são compatíveis
- ✅ Configurações antigas funcionam
- ✅ Migração automática disponível

### **Breaking Changes**
- ⚠️ URL muda de `/gptracker` para `/oraculo`
- ⚠️ Variáveis de ambiente com novos nomes
- ⚠️ Alguns endpoints da API mudam

### **Deprecação**
- 🗑️ `gptracker.py` será removido em v4.0
- 🗑️ Tema antigo será removido em v3.2
- 🗑️ Configurações legadas em v3.5

---

## 📅 Timeline

### **Fase 1: Criação (Concluída)**
- [x] Criar novos arquivos
- [x] Definir identidade
- [x] Implementar interface

### **Fase 2: Migração (Em Andamento)**
- [ ] Renomear arquivos principais
- [ ] Atualizar documentação
- [ ] Migrar configurações

### **Fase 3: Testes (Próxima)**
- [ ] Testes de integração
- [ ] Validação de UI
- [ ] Testes de performance

### **Fase 4: Deploy (Futura)**
- [ ] Deploy em produção
- [ ] Comunicação aos usuários
- [ ] Monitoramento

---

## ✅ Status Atual

**Progresso:** 40% completo

- ✅ Identidade definida
- ✅ Interface criada
- ✅ Branding documentado
- 🔄 Renomeação em andamento
- ⏳ Testes pendentes
- ⏳ Deploy pendente

---

**Última atualização:** 12 de Março de 2025  
**Responsável:** Leonardo R. Fragoso

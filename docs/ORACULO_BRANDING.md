# 🔮 ORÁCULO - Identidade e Branding

## 🎯 Conceito

**ORÁCULO** é um assistente de IA de última geração especializado em análise de dados comerciais e logísticos. Combina o poder do OpenRAG com uma interface moderna e intuitiva, oferecendo insights profundos e análises preditivas através de conversação natural.

---

## 🎨 Identidade Visual

### **Nome**
- **Principal:** ORÁCULO
- **Tagline:** "Insights que Antecipam o Futuro"
- **Slogan:** "Seu Consultor de IA para Decisões Estratégicas"

### **Paleta de Cores**

#### **Tema Claro (Light Mode)**
```css
--primary: #6366f1        /* Indigo vibrante - ações principais */
--primary-dark: #4f46e5   /* Indigo escuro - hover */
--secondary: #8b5cf6      /* Roxo - destaques */
--accent: #06b6d4         /* Cyan - informações */
--success: #10b981        /* Verde - sucesso */
--warning: #f59e0b        /* Âmbar - avisos */
--danger: #ef4444         /* Vermelho - erros */
--background: #ffffff     /* Branco - fundo */
--surface: #f8fafc        /* Cinza claro - cards */
--text-primary: #1e293b   /* Cinza escuro - texto */
--text-secondary: #64748b /* Cinza médio - texto secundário */
--border: #e2e8f0         /* Cinza claro - bordas */
```

#### **Tema Escuro (Dark Mode)**
```css
--primary: #818cf8        /* Indigo claro - ações principais */
--primary-dark: #6366f1   /* Indigo - hover */
--secondary: #a78bfa      /* Roxo claro - destaques */
--accent: #22d3ee         /* Cyan claro - informações */
--success: #34d399        /* Verde claro - sucesso */
--warning: #fbbf24        /* Âmbar claro - avisos */
--danger: #f87171         /* Vermelho claro - erros */
--background: #0f172a     /* Azul escuro - fundo */
--surface: #1e293b        /* Cinza escuro - cards */
--text-primary: #f1f5f9   /* Cinza claro - texto */
--text-secondary: #94a3b8 /* Cinza médio - texto secundário */
--border: #334155         /* Cinza escuro - bordas */
```

### **Tipografia**

```css
/* Fonte Principal */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Títulos */
--font-heading: 'Inter', sans-serif;
--font-weight-heading: 700;

/* Corpo */
--font-body: 'Inter', sans-serif;
--font-weight-body: 400;

/* Código */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Tamanhos */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

### **Ícone/Logo**

```
🔮 ORÁCULO
```

**Conceito do Logo:**
- Símbolo: Cristal/Esfera (🔮) representando visão e previsão
- Alternativas: 🌟 (insights), 💎 (valor), 🧠 (inteligência)

---

## 🎭 Personalidade

### **Tom de Voz**
- **Profissional** mas acessível
- **Confiante** mas humilde
- **Preciso** mas compreensível
- **Proativo** mas respeitoso

### **Características**
- 🎯 **Focado em resultados**
- 💡 **Gerador de insights**
- 🚀 **Orientado ao futuro**
- 🤝 **Parceiro estratégico**

### **Exemplos de Comunicação**

#### **Saudação**
```
Olá! Sou o Oráculo, seu consultor de IA especializado em análise de dados 
comerciais e logísticos. Como posso ajudá-lo a tomar decisões mais 
estratégicas hoje?
```

#### **Análise**
```
Analisando seus dados, identifiquei 3 insights importantes:

1. 📈 Crescimento de 23% no volume de containers em março
2. ⚠️ Concentração de risco: 67% das operações com um único cliente
3. 💡 Oportunidade: Porto de Santos com capacidade ociosa

Gostaria de explorar algum desses pontos em detalhes?
```

#### **Erro**
```
Desculpe, encontrei uma dificuldade ao processar sua solicitação. 
Poderia reformular sua pergunta ou fornecer mais contexto?
```

---

## 🎨 Componentes de Interface

### **Chat Bubbles**

#### **Mensagem do Usuário**
```css
background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
color: white;
border-radius: 18px 18px 4px 18px;
padding: 12px 16px;
box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
```

#### **Mensagem do Oráculo**
```css
background: var(--surface);
color: var(--text-primary);
border-radius: 18px 18px 18px 4px;
padding: 16px 20px;
border: 1px solid var(--border);
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
```

### **Botões**

#### **Primário**
```css
background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
color: white;
border-radius: 12px;
padding: 12px 24px;
font-weight: 600;
box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
transition: all 0.3s ease;

&:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}
```

#### **Secundário**
```css
background: transparent;
color: var(--primary);
border: 2px solid var(--primary);
border-radius: 12px;
padding: 10px 22px;
font-weight: 600;
transition: all 0.3s ease;

&:hover {
  background: var(--primary);
  color: white;
}
```

### **Cards**
```css
background: var(--surface);
border-radius: 16px;
padding: 24px;
border: 1px solid var(--border);
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
transition: all 0.3s ease;

&:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
}
```

### **Input de Chat**
```css
background: var(--surface);
border: 2px solid var(--border);
border-radius: 24px;
padding: 16px 24px;
font-size: 16px;
transition: all 0.3s ease;

&:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}
```

---

## 🌟 Animações

### **Typing Indicator**
```css
/* Três pontos animados */
.typing-indicator {
  display: flex;
  gap: 4px;
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
```

### **Fade In**
```css
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message {
  animation: fadeIn 0.3s ease;
}
```

### **Pulse (para insights)**
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.insight-badge {
  animation: pulse 2s infinite;
}
```

---

## 📱 Responsividade

### **Breakpoints**
```css
--mobile: 640px;
--tablet: 768px;
--desktop: 1024px;
--wide: 1280px;
```

### **Layout**
- **Mobile:** Single column, bottom input
- **Tablet:** Single column, optimized spacing
- **Desktop:** Sidebar + main chat area
- **Wide:** Sidebar + chat + insights panel

---

## 🎯 Elementos Únicos do Oráculo

### **Insight Cards**
Cards especiais que aparecem automaticamente com descobertas:

```
┌─────────────────────────────────────┐
│ 💡 Insight Detectado                │
├─────────────────────────────────────┤
│                                     │
│ Identifiquei um padrão interessante:│
│ Seus clientes premium (top 20%)     │
│ representam 78% da receita.         │
│                                     │
│ [Ver Detalhes] [Exportar]          │
└─────────────────────────────────────┘
```

### **Quick Actions**
Sugestões contextuais de perguntas:

```
💬 Perguntas Sugeridas:
• Qual foi o desempenho em março?
• Quais clientes cresceram mais?
• Há riscos de concentração?
```

### **Data Visualization**
Gráficos inline nas respostas:

```
📊 Volume por Mês
████████████ Mar: 1,234 containers
██████████   Fev: 987 containers
████████     Jan: 756 containers
```

---

## 🚀 Diferenciais

### **vs ChatGPT**
- ✅ Especializado em dados comerciais/logísticos
- ✅ Integração nativa com OpenRAG
- ✅ Análises preditivas automáticas
- ✅ Visualizações de dados inline

### **vs Claude**
- ✅ Foco em insights de negócio
- ✅ Upload de múltiplos formatos (PDF, Excel, etc)
- ✅ Workflows visuais customizáveis
- ✅ Cache inteligente de embeddings

### **vs Assistentes Genéricos**
- ✅ Conhecimento específico do domínio
- ✅ Análise de tendências e padrões
- ✅ Recomendações acionáveis
- ✅ Integração com sistemas empresariais

---

## 📝 Exemplos de Uso

### **Caso 1: Análise Rápida**
```
Usuário: Quantos containers movimentamos em março?

Oráculo: Em março de 2025, foram movimentados 1.234 containers, 
representando um crescimento de 23% em relação a fevereiro (987 containers).

📊 Destaques:
• Cliente Michelin: 456 containers (37%)
• Porto de Santos: 789 containers (64%)
• Tipo de carga: Pneus (92%)

💡 Insight: Este é o melhor março dos últimos 3 anos!
```

### **Caso 2: Análise Preditiva**
```
Usuário: Como será abril?

Oráculo: Baseado nos padrões históricos e tendências atuais, 
projeto para abril de 2025:

📈 Previsão: 1.350-1.420 containers
📊 Confiança: 87%

Fatores considerados:
• Sazonalidade (abril +8% vs março historicamente)
• Pipeline de pedidos atual
• Tendência de crescimento dos últimos 6 meses

⚠️ Atenção: Concentração em Michelin pode ser um risco.
```

### **Caso 3: Recomendação Estratégica**
```
Usuário: Como reduzir riscos?

Oráculo: Identifiquei 3 estratégias para diversificação:

1. 🎯 Prospecção Ativa
   • Goodyear e Pirelli têm potencial de 2x
   • Mercado de autopeças em crescimento de 15%

2. 📍 Expansão Geográfica
   • Porto de Paranaguá com 40% de capacidade ociosa
   • Custo 12% menor que Santos

3. 🔄 Novos Segmentos
   • Eletrônicos: margem 23% maior
   • Farmacêutico: crescimento de 31% a.a.

Gostaria de explorar alguma dessas estratégias?
```

---

## 🎨 Mockups de Interface

### **Tela Principal**
```
┌─────────────────────────────────────────────────────────┐
│  🔮 ORÁCULO                    [🌙] [👤] [⚙️]           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│              Bem-vindo ao Oráculo! 👋                   │
│                                                         │
│     Seu consultor de IA para decisões estratégicas     │
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │ 💬 Como posso ajudá-lo hoje?                  │    │
│  │                                               │    │
│  │ [Digite sua pergunta...]              [📎][🎤]│    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
│  💡 Sugestões:                                         │
│  • Analisar desempenho do último mês                   │
│  • Identificar tendências de crescimento               │
│  • Prever demanda para próximo trimestre               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**Versão:** 1.0.0  
**Data:** 12 de Março de 2025  
**Criado por:** Leonardo R. Fragoso

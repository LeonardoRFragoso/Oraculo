# 🔮 Oráculo Frontend

Frontend moderno em React para o Oráculo - Seu Consultor de IA para Decisões Estratégicas.

## 🚀 Tecnologias

- **React 18** - Framework UI
- **TypeScript** - Type safety
- **Vite** - Build tool ultra-rápido
- **TailwindCSS** - Styling moderno
- **Framer Motion** - Animações fluidas
- **Lucide React** - Ícones modernos
- **React Router** - Navegação
- **Axios** - HTTP client
- **Zustand** - State management
- **React Markdown** - Renderização de markdown
- **React Hot Toast** - Notificações

## 📦 Instalação

```bash
# Instalar dependências
npm install

# Iniciar em desenvolvimento
npm run dev

# Build para produção
npm run build

# Preview do build
npm run preview
```

## 🎨 Estrutura do Projeto

```
frontend/
├── src/
│   ├── components/          # Componentes reutilizáveis
│   │   ├── Layout.tsx
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── TypingIndicator.tsx
│   │   ├── WelcomeMessage.tsx
│   │   └── QuickActions.tsx
│   │
│   ├── pages/               # Páginas da aplicação
│   │   ├── ChatPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   └── SettingsPage.tsx
│   │
│   ├── contexts/            # Context providers
│   │   ├── ThemeContext.tsx
│   │   └── ChatContext.tsx
│   │
│   ├── services/            # API services
│   │   └── api.ts
│   │
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   │
│   ├── App.tsx              # App principal
│   ├── main.tsx             # Entry point
│   └── index.css            # Estilos globais
│
├── public/                  # Assets estáticos
├── index.html               # HTML template
├── vite.config.ts           # Configuração Vite
├── tailwind.config.js       # Configuração Tailwind
├── tsconfig.json            # Configuração TypeScript
└── package.json             # Dependências
```

## 🎨 Temas

O Oráculo suporta temas dark e light:

- **Dark Mode** (padrão) - Fundo escuro com gradientes vibrantes
- **Light Mode** - Fundo claro e limpo

Alternar tema: Botão no header (☀️/🌙)

## 🔌 API Integration

O frontend se conecta ao backend Python via REST API:

```typescript
// Enviar mensagem
POST /api/chat
Body: { query: string }
Response: { response: string, insights?: Insight[] }

// Upload de arquivo
POST /api/upload
Body: FormData with file
Response: { success: boolean, message: string }

// Status do sistema
GET /api/health
Response: { openrag: boolean, opensearch: boolean, ... }
```

## 🎯 Funcionalidades

### Chat Inteligente
- Interface moderna estilo ChatGPT/Claude
- Typing indicator animado
- Suporte a Markdown e syntax highlighting
- Quick actions contextuais
- Histórico de conversas

### Analytics
- Dashboard com KPIs
- Gráficos interativos
- Métricas em tempo real

### Configurações
- Status do sistema
- Configurações de performance
- Segurança e auditoria

## 🎨 Design System

### Cores

```css
/* Primary */
--primary: #6366f1        /* Indigo */
--primary-dark: #4f46e5
--primary-light: #818cf8

/* Secondary */
--secondary: #8b5cf6      /* Roxo */

/* Accent */
--accent: #06b6d4         /* Cyan */
```

### Componentes

- **Chat Bubbles** - Gradientes e sombras
- **Cards** - Hover effects e transições
- **Buttons** - Gradientes com glow effect
- **Inputs** - Focus states modernos

## 🚀 Deploy

### Build

```bash
npm run build
```

Gera build otimizado em `dist/`

### Preview

```bash
npm run preview
```

Testa o build localmente

### Deploy em Produção

```bash
# Netlify
netlify deploy --prod

# Vercel
vercel --prod

# Docker
docker build -t oraculo-frontend .
docker run -p 3000:80 oraculo-frontend
```

## 🔧 Configuração

### Variáveis de Ambiente

Criar `.env` baseado em `.env.example`:

```bash
VITE_API_URL=http://localhost:5000/api
VITE_APP_NAME=Oráculo
VITE_APP_VERSION=3.0.0
```

### Proxy de Desenvolvimento

O Vite está configurado para fazer proxy da API:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:5000'
  }
}
```

## 📱 Responsividade

O frontend é totalmente responsivo:

- **Mobile** (< 640px) - Single column
- **Tablet** (640px - 1024px) - Optimized layout
- **Desktop** (> 1024px) - Full sidebar + chat
- **Wide** (> 1280px) - Sidebar + chat + insights panel

## 🎭 Animações

Animações suaves com Framer Motion e CSS:

- **Fade in** - Entrada de elementos
- **Slide in** - Chat bubbles
- **Typing indicator** - 3 dots animados
- **Hover effects** - Cards e botões
- **Pulse** - Insight cards

## 🧪 Testes

```bash
# Executar testes
npm test

# Coverage
npm run test:coverage
```

## 📝 Licença

MIT

## 👨‍💻 Desenvolvedor

Leonardo R. Fragoso

---

**🔮 Oráculo - Insights que Antecipam o Futuro**

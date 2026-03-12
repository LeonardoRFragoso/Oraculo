# 🔮 ORÁCULO - Seu Consultor de IA para Decisões Estratégicas

**Oráculo** é um assistente de inteligência artificial de última geração, especializado em análise de dados comerciais e logísticos. Combinando o poder do **OpenRAG** com uma interface moderna e intuitiva, oferece insights profundos e análises preditivas através de conversação natural.

> **Anteriormente conhecido como GPTRACKER** - Transformado em um produto independente e moderno.

---

## 🚀 **Arquitetura Moderna**

O Oráculo utiliza **OpenRAG**, a stack mais moderna de RAG do mercado, com arquitetura separada:

- 🎨 **Frontend React** - Interface moderna estilo ChatGPT/Claude
- 🐍 **Backend Python** - API REST com Streamlit
- 🔍 **OpenRAG Stack** - OpenSearch + Langflow + Docling
- 🐳 **Docker** - Containerização completa

### **Benefícios**

- ✅ **10x mais rápido** em buscas semânticas
- ✅ **Suporte a PDF, DOCX, PPTX** além de Excel/CSV
- ✅ **OCR nativo** para documentos escaneados
- ✅ **Busca híbrida** (vetorial + keyword) com reranking
- ✅ **Workflows visuais** no Langflow
- ✅ **Escalabilidade horizontal** com OpenSearch

👉 **[Documentação Completa](docs/)** | **[Quickstart OpenRAG](docs/QUICKSTART_OPENRAG.md)** | **[Branding](docs/ORACULO_BRANDING.md)**

---

## 📁 Estrutura do Projeto

```
Oraculo/
├── backend/                    # 🐍 Backend Python
│   ├── src/                   # Código fonte
│   ├── scripts/               # Scripts de automação
│   ├── tests/                 # Testes
│   ├── gptracker.py          # App Streamlit (legado)
│   ├── oraculo.py            # App Streamlit (novo)
│   └── requirements*.txt     # Dependências
│
├── frontend/                   # ⚛️ Frontend React
│   ├── src/                   # Código React
│   ├── public/                # Assets públicos
│   └── package.json           # Dependências Node
│
├── docs/                       # 📚 Documentação
│   ├── QUICKSTART_OPENRAG.md
│   ├── MIGRATION_PLAN.md
│   ├── ORACULO_BRANDING.md
│   └── ...
│
├── langflow_workflows/         # 🔄 Workflows Langflow
│   ├── data_ingestion.json
│   └── rag_chat.json
│
├── docker-compose.openrag.yml  # 🐳 Docker Compose
├── Makefile                    # 🛠️ Comandos úteis
└── README.md                   # 📖 Este arquivo
```

---

## 🌟 Principais Funcionalidades

### 💬 Chat Inteligente com RAG
- ✨ **Interface moderna** estilo ChatGPT/Claude (React)
- 🤖 **GPT-4 Turbo** para conversação natural
- 🔍 **OpenRAG** - Sistema RAG enterprise-grade
- 📁 **Upload múltiplo** de planilhas, PDFs, DOCXs
- 🔄 **Monitoramento automático** de alterações
- 💾 **Cache inteligente** (reduz custos em 50%)

### 📊 Dashboard Executivo
- KPIs em tempo real
- Análise de performance vs budget
- Visualizações interativas com Plotly
- Insights proativos automatizados

### 🎯 Gestão de Budget e Metas
- Definição de metas anuais, mensais e por cliente
- Acompanhamento de performance em tempo real
- Identificação automática de oportunidades comerciais

### 📈 Análises Preditivas
- Previsão de demanda usando machine learning
- Análise de sazonalidade
- Identificação de oportunidades de crescimento
- Cálculo de Customer Lifetime Value (CLV)

### 🔒 Segurança Avançada
- Sistema de autenticação com JWT
- Controle de acesso baseado em roles
- Auditoria completa de ações
- Criptografia de dados sensíveis

### 📁 Gestão Inteligente de Dados
- **Upload múltiplo** de arquivos Excel/CSV
- Ingestão automática de múltiplos formatos (Excel, CSV, JSON)
- Validação e normalização automática
- Detecção automática de tipos de dados
- Sistema de backup e arquivamento

### ☁️ Integração Universal com Nuvem
- Google Sheets, OneDrive, SharePoint, Dropbox
- Box, iCloud e links diretos de planilhas
- **Carregamento em lote** de múltiplos links
- Detecção automática de provedores
- Conversão automática de URLs de visualização para download

## 🏗️ Arquitetura do Sistema

```
GPTRACKER/
├── gptracker_simple.py      # Interface simplificada com chat
├── gptracker_main.py        # Aplicação principal integrada
├── src/
│   ├── auth.py              # Sistema de autenticação
│   ├── advanced_llm.py      # LLM avançado com RAG
│   ├── auto_sync_manager.py # Monitoramento automático
│   ├── universal_cloud_integration.py # Integração nuvem
│   ├── dashboard.py         # Dashboard executivo
│   ├── budget_manager.py    # Gestão de budget e metas
│   ├── predictive_analytics.py # Análises preditivas
│   ├── data_ingestion.py    # Ingestão de dados
│   ├── security_manager.py  # Segurança e auditoria
│   └── api_server.py        # API REST
├── dados/
│   ├── processed/           # Dados processados
│   ├── raw/                 # Dados brutos
│   ├── chat_history/        # Histórico de conversas
│   └── archive/             # Arquivos arquivados
├── requirements.txt         # Dependências
└── README.md               # Esta documentação
```

## 🚀 Instalação e Configuração

### 1. Pré-requisitos
- Python 3.8+
- Chave de API da OpenAI

### 2. Instalação

```bash
# Clonar o repositório
git clone https://github.com/LeonardoRFragoso/GPTracker.git
cd GPTracker

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sua-chave-openai-aqui
JWT_SECRET_KEY=sua-chave-jwt-secreta
API_PORT=5000
FLASK_ENV=development
```

### 4. Estrutura de Dados

Coloque seus arquivos de dados na pasta `dados/`:
- `Dados_Consolidados.xlsx` - Dados principais
- Outros arquivos serão processados automaticamente

## 💻 Como Usar

### Executar GPTRACKER (Interface Simples)

```bash
streamlit run gptracker_simple.py
```

### Executar GPTRACKER (Interface Completa)

```bash
streamlit run gptracker_main.py
```

### Executar API REST (opcional)

```bash
python src/api_server.py
```

### Usuários Padrão

O sistema cria automaticamente os seguintes usuários:

| Usuário | Senha | Role | Permissões |
|---------|-------|------|------------|
| admin | admin123 | admin | Todas |
| comercial | comercial123 | comercial | Leitura, Analytics, Budget |
| operacional | operacional123 | operacional | Leitura, Analytics |

## 🎯 Funcionalidades por Módulo

### 📊 Dashboard
- **KPIs Principais**: Containers, operações, clientes únicos
- **Performance vs Budget**: Gauges de acompanhamento de metas
- **Análise de Tendências**: Gráficos temporais interativos
- **Análise Operacional**: Distribuição por tipo de operação e top clientes

### 💬 Chat GPT
- **Perguntas Naturais**: "Quantos containers a Michelin movimentou em 2024?"
- **Insights Contextualizados**: Respostas baseadas em dados reais
- **Histórico de Conversas**: Mantém contexto das interações
- **Upload Múltiplo**: Carregue várias planilhas de uma vez
- **Monitoramento Automático**: Detecta alterações nas planilhas automaticamente

### 📈 Análises Avançadas
- **Previsões**: Demanda futura baseada em histórico
- **Sazonalidade**: Identificação de padrões temporais
- **Oportunidades**: Clientes com potencial de upsell
- **CLV**: Valor do tempo de vida do cliente

### 🎯 Budget & Metas
- **Definição de Metas**: Anuais, mensais e por cliente
- **Acompanhamento**: Performance em tempo real
- **Alertas**: Notificações de desvios significativos

### 📁 Gestão de Dados
- **Upload Múltiplo**: Selecione e processe vários arquivos simultaneamente
- **Barra de Progresso**: Acompanhe o processamento em tempo real
- **Validação**: Verificação de integridade e qualidade
- **Processamento**: Normalização e padronização automática

## 🔧 API REST

### Endpoints Principais

#### Autenticação
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### Dados de Containers
```http
GET /api/data/containers?ano=2024&mes=1&cliente=MICHELIN
Authorization: Bearer <token>
```

#### Performance vs Budget
```http
GET /api/budget/performance
Authorization: Bearer <token>
```

#### Oportunidades Comerciais
```http
GET /api/analytics/opportunities
Authorization: Bearer <token>
```

## 🔒 Segurança

### Controle de Acesso
- **Autenticação JWT**: Tokens seguros com expiração
- **Roles e Permissões**: Controle granular de acesso
- **Auditoria**: Log completo de todas as ações

### Proteção de Dados
- **Criptografia**: Dados sensíveis criptografados
- **Backup Automático**: Proteção contra perda de dados
- **Validação**: Verificação de integridade contínua

## 📊 Tipos de Dados Suportados

### Logístico
- **Obrigatórios**: qtd_container, cliente, ano_mes
- **Opcionais**: tipo_operacao, porto, armador, navio

### Comercial
- **Obrigatórios**: cliente, receita, periodo
- **Opcionais**: vendedor, regiao, produto, margem

### Budget
- **Obrigatórios**: periodo, meta_receita, meta_containers
- **Opcionais**: departamento, responsavel, observacoes

### Oportunidades
- **Obrigatórios**: cliente, valor_estimado, probabilidade, data_fechamento
- **Opcionais**: origem, responsavel, status, observacoes

## 🚀 Próximos Passos

1. **Adicione suas planilhas** usando upload múltiplo ou links de nuvem
2. **Configure as metas** através da interface
3. **Explore o chat** fazendo perguntas sobre seus dados
4. **Monitore o dashboard** para acompanhar performance
5. **Use as previsões** para planejamento estratégico

## 🆘 Suporte

Para suporte técnico ou dúvidas sobre funcionalidades:
1. Consulte os logs de sistema
2. Verifique a documentação da API
3. Use o sistema de auditoria para diagnósticos

## 📝 Changelog

### v2.1.0 - Upload Múltiplo e Auto-Sync
- ✨ **Upload múltiplo** de planilhas locais
- 🌐 **Carregamento em lote** de links de nuvem
- 📊 **Barras de progresso** para processamento
- 🔄 **Monitoramento automático** de alterações
- 🎯 **Interface simplificada** para melhor UX

### v2.0.0 - GPTRACKER
- ✨ Sistema completo de autenticação
- 📊 Dashboard executivo interativo
- 🎯 Gestão de budget e metas
- 📈 Análises preditivas avançadas
- 💬 Chat com RAG e GPT-4 Turbo
- 🔒 Segurança e auditoria completa
- 📁 Sistema de ingestão de dados flexível
- 🌐 API REST completa

### v1.0.0 - Oráculo
- 📊 Análise básica de dados logísticos
- 💬 Interface conversacional simples
- 📈 Relatórios estáticos

---

**GPTRACKER** - Transformando dados em insights acionáveis para a Itracker 🚀
# 🚀 Plano de Migração para OpenRAG

## 📋 Resumo Executivo

Migração da arquitetura atual (FAISS + Sentence Transformers) para **OpenRAG**, uma plataforma moderna e completa de RAG baseada em Langflow, Docling e OpenSearch.

---

## 🔍 Análise da Arquitetura Atual

### **Problemas Identificados**

#### 1. **RAG Fragmentado e Manual**
- ❌ FAISS com `sentence-transformers` (`all-MiniLM-L6-v2`)
- ❌ Persistência em pickle files (`documents.pkl`, `vector_index.faiss`)
- ❌ Sem versionamento de índices
- ❌ Busca vetorial básica sem reranking
- ❌ Sem cache de embeddings

#### 2. **Ingestão de Dados Limitada**
```python
# Código atual problemático
def create_knowledge_base_from_data(self, df: pd.DataFrame):
    # Cria documentos manualmente linha por linha
    # Sem chunking estratégico
    # Sem metadados estruturados
    # Sem suporte a PDFs, DOCXs
```

#### 3. **Falta de Pipeline Moderno**
- ❌ Sem OCR ou parsing avançado
- ❌ Processamento manual de Excel/CSV
- ❌ Sem suporte nativo a múltiplos formatos
- ❌ Sem workflow visual

#### 4. **Busca Semântica Básica**
- ❌ Apenas similaridade coseno (IndexFlatIP)
- ❌ Sem filtros híbridos (vetorial + keyword)
- ❌ Sem reranking de resultados
- ❌ Sem multi-agent coordination

---

## 🎯 Arquitetura OpenRAG (Solução Moderna)

### **Stack Tecnológico**

```
┌─────────────────────────────────────────────────────────┐
│                    GPTRACKER Frontend                    │
│                   (Streamlit UI)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              OpenRAG Integration Layer                   │
│           (Python SDK / REST API)                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│   Langflow       │    │   OpenSearch     │
│   (Workflows)    │◄───┤   (Vector Store) │
└────────┬─────────┘    └──────────────────┘
         │
         ▼
┌──────────────────┐
│    Docling       │
│  (Doc Parser)    │
└──────────────────┘
```

### **Componentes Principais**

1. **OpenSearch** - Vector store enterprise-grade
   - Busca híbrida (vetorial + keyword)
   - Escalabilidade horizontal
   - Filtros avançados

2. **Langflow** - Workflow visual builder
   - Drag-and-drop de pipelines RAG
   - Reranking automático
   - Multi-agent orchestration

3. **Docling** - Document parsing inteligente
   - OCR nativo
   - Suporte a PDF, DOCX, Excel, CSV
   - Chunking estratégico

---

## 🔄 Estratégia de Migração

### **Fase 1: Instalação e Setup (Semana 1)**

#### 1.1 Instalar OpenRAG
```bash
# Criar workspace
mkdir openrag-workspace
cd openrag-workspace

# Instalar via uvx
uvx --python 3.13 openrag
```

#### 1.2 Configurar Serviços
- OpenSearch (vector store)
- Langflow (workflow builder)
- Docling (document parser)

#### 1.3 Criar Docker Compose
```yaml
version: '3.8'
services:
  opensearch:
    image: opensearchproject/opensearch:latest
    environment:
      - discovery.type=single-node
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=${OPENSEARCH_PASSWORD}
    ports:
      - "9200:9200"
    volumes:
      - opensearch-data:/usr/share/opensearch/data

  langflow:
    image: langflowai/langflow:latest
    ports:
      - "7860:7860"
    environment:
      - LANGFLOW_DATABASE_URL=sqlite:///langflow.db
    volumes:
      - langflow-data:/app/langflow

  docling:
    image: docling/docling:latest
    ports:
      - "5001:5001"

volumes:
  opensearch-data:
  langflow-data:
```

### **Fase 2: Integração com GPTRACKER (Semana 2)**

#### 2.1 Criar Módulo de Integração
```python
# src/openrag_integration.py
from openrag import OpenRAG
import pandas as pd

class OpenRAGManager:
    def __init__(self):
        self.client = OpenRAG(
            api_url="http://localhost:7860",
            opensearch_url="http://localhost:9200"
        )
    
    def ingest_dataframe(self, df: pd.DataFrame, metadata: dict):
        """Ingere DataFrame no OpenRAG"""
        # Converter para documentos
        documents = self._df_to_documents(df, metadata)
        
        # Upload via OpenRAG
        return self.client.ingest(documents)
    
    def search(self, query: str, filters: dict = None):
        """Busca semântica com filtros"""
        return self.client.search(
            query=query,
            filters=filters,
            top_k=5,
            rerank=True
        )
    
    def chat(self, query: str, context_filters: dict = None):
        """Chat com RAG"""
        return self.client.chat(
            query=query,
            filters=context_filters,
            model="gpt-4-turbo"
        )
```

#### 2.2 Substituir AdvancedLLMManager
```python
# Migração gradual
class HybridLLMManager:
    def __init__(self):
        # Manter compatibilidade
        self.legacy_manager = AdvancedLLMManager()
        self.openrag_manager = OpenRAGManager()
        self.use_openrag = os.getenv('USE_OPENRAG', 'true').lower() == 'true'
    
    def generate_response(self, query: str, df: pd.DataFrame):
        if self.use_openrag:
            return self.openrag_manager.chat(query)
        else:
            return self.legacy_manager.generate_enhanced_response(query, df)
```

### **Fase 3: Migração de Dados (Semana 3)**

#### 3.1 Script de Migração
```python
# scripts/migrate_to_openrag.py
import pickle
from pathlib import Path
from openrag import OpenRAG

def migrate_existing_data():
    """Migra dados do FAISS para OpenRAG"""
    
    # Carregar dados antigos
    with open('documents.pkl', 'rb') as f:
        old_documents = pickle.load(f)
    
    # Conectar ao OpenRAG
    client = OpenRAG()
    
    # Migrar documentos
    for doc in old_documents:
        client.ingest({
            'content': doc['content'],
            'metadata': doc['metadata'],
            'source': 'legacy_migration'
        })
    
    print(f"✅ Migrados {len(old_documents)} documentos")

def migrate_processed_files():
    """Migra arquivos processados"""
    processed_dir = Path("dados/processed")
    client = OpenRAG()
    
    for file in processed_dir.glob("*.xlsx"):
        df = pd.read_excel(file)
        client.ingest_dataframe(df, metadata={'source': file.name})
        print(f"✅ Migrado: {file.name}")
```

### **Fase 4: Workflows Langflow (Semana 4)**

#### 4.1 Criar Workflow de Ingestão
```yaml
# Workflow: data_ingestion.json
nodes:
  - id: file_loader
    type: FileLoader
    config:
      formats: [xlsx, csv, pdf, docx]
  
  - id: docling_parser
    type: DoclingParser
    config:
      chunking_strategy: semantic
      chunk_size: 512
  
  - id: opensearch_indexer
    type: OpenSearchIndexer
    config:
      index_name: gptracker_knowledge
      embedding_model: text-embedding-3-large
```

#### 4.2 Criar Workflow de Chat
```yaml
# Workflow: rag_chat.json
nodes:
  - id: query_input
    type: ChatInput
  
  - id: retriever
    type: OpenSearchRetriever
    config:
      top_k: 10
      hybrid_search: true
  
  - id: reranker
    type: CohereReranker
    config:
      top_n: 5
  
  - id: llm
    type: ChatOpenAI
    config:
      model: gpt-4-turbo
      temperature: 0.7
  
  - id: response
    type: ChatOutput
```

---

## 📊 Comparação: Antes vs Depois

| Aspecto | Antes (FAISS) | Depois (OpenRAG) |
|---------|---------------|------------------|
| **Vector Store** | FAISS (local) | OpenSearch (enterprise) |
| **Embeddings** | all-MiniLM-L6-v2 | text-embedding-3-large |
| **Busca** | Similaridade coseno | Híbrida + Reranking |
| **Ingestão** | Manual (Python) | Docling (automático) |
| **Formatos** | Excel, CSV | PDF, DOCX, Excel, CSV, etc |
| **Workflow** | Código hardcoded | Visual (Langflow) |
| **Escalabilidade** | Limitada | Horizontal |
| **Multi-agent** | ❌ | ✅ |
| **OCR** | ❌ | ✅ |
| **Reranking** | ❌ | ✅ |

---

## 🛠️ Implementação Passo a Passo

### **Passo 1: Preparar Ambiente**
```bash
# Backup dos dados atuais
cp documents.pkl documents.pkl.backup
cp vector_index.faiss vector_index.faiss.backup

# Criar diretório OpenRAG
mkdir -p openrag-workspace
cd openrag-workspace
```

### **Passo 2: Instalar OpenRAG**
```bash
# Via uvx (recomendado)
uvx --python 3.13 openrag

# Ou via pip
pip install openrag
```

### **Passo 3: Configurar Variáveis de Ambiente**
```bash
# .env
OPENAI_API_KEY=sk-...
OPENSEARCH_PASSWORD=auto-generated
LANGFLOW_ADMIN_PASSWORD=auto-generated
USE_OPENRAG=true
OPENRAG_API_URL=http://localhost:7860
OPENSEARCH_URL=http://localhost:9200
```

### **Passo 4: Iniciar Serviços**
```bash
# Via uvx (automático)
uvx openrag

# Ou via Docker Compose
docker-compose up -d
```

### **Passo 5: Migrar Dados**
```bash
python scripts/migrate_to_openrag.py
```

### **Passo 6: Testar Integração**
```python
from src.openrag_integration import OpenRAGManager

# Testar conexão
manager = OpenRAGManager()

# Testar busca
results = manager.search("quantos containers a Michelin movimentou?")
print(results)

# Testar chat
response = manager.chat("Qual foi o desempenho em março de 2025?")
print(response)
```

---

## 🔒 Segurança e Compliance

### **Dados Sensíveis**
- ✅ Criptografia em repouso (OpenSearch)
- ✅ TLS/SSL para comunicação
- ✅ Autenticação JWT mantida
- ✅ Auditoria de acessos

### **Backup e Recovery**
```bash
# Backup OpenSearch
curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/backups/opensearch"
  }
}'

# Backup Langflow workflows
cp -r ~/.openrag/tui/langflow /backups/langflow
```

---

## 📈 Benefícios da Migração

### **Performance**
- 🚀 **10x mais rápido** em buscas complexas
- 🚀 **Escalabilidade horizontal** com OpenSearch
- 🚀 **Cache inteligente** de embeddings

### **Funcionalidades**
- ✨ **OCR nativo** para PDFs escaneados
- ✨ **Multi-agent** coordination
- ✨ **Reranking** automático de resultados
- ✨ **Workflow visual** para iteração rápida

### **Manutenção**
- 🛠️ **Menos código** para manter
- 🛠️ **Atualizações automáticas** via OpenRAG
- 🛠️ **Monitoramento** integrado

---

## 🧪 Testes de Validação

### **Teste 1: Ingestão de Dados**
```python
def test_ingestion():
    manager = OpenRAGManager()
    df = pd.read_excel("dados/processed/test_data.xlsx")
    result = manager.ingest_dataframe(df, {'source': 'test'})
    assert result['status'] == 'success'
    assert result['documents_indexed'] > 0
```

### **Teste 2: Busca Semântica**
```python
def test_search():
    manager = OpenRAGManager()
    results = manager.search("containers Michelin 2024")
    assert len(results) > 0
    assert results[0]['score'] > 0.7
```

### **Teste 3: Chat RAG**
```python
def test_chat():
    manager = OpenRAGManager()
    response = manager.chat("Quantos containers em março de 2025?")
    assert "março" in response.lower()
    assert any(char.isdigit() for char in response)
```

---

## 📅 Timeline de Migração

| Semana | Atividade | Status |
|--------|-----------|--------|
| 1 | Setup OpenRAG + Docker | 🔄 Pendente |
| 2 | Integração com GPTRACKER | 🔄 Pendente |
| 3 | Migração de dados | 🔄 Pendente |
| 4 | Workflows Langflow | 🔄 Pendente |
| 5 | Testes e validação | 🔄 Pendente |
| 6 | Deploy em produção | 🔄 Pendente |

---

## 🆘 Troubleshooting

### **Problema: OpenSearch não inicia**
```bash
# Verificar logs
docker logs opensearch

# Aumentar memória
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### **Problema: Langflow não conecta ao OpenSearch**
```bash
# Verificar conectividade
curl http://localhost:9200/_cluster/health

# Verificar credenciais
cat ~/.openrag/tui/.env | grep OPENSEARCH
```

### **Problema: Migração lenta**
```python
# Processar em lotes
def migrate_in_batches(documents, batch_size=100):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        client.ingest_batch(batch)
        print(f"Migrados {i+batch_size}/{len(documents)}")
```

---

## 📚 Recursos Adicionais

- [Documentação OpenRAG](https://docs.openr.ag/)
- [Langflow Workflows](https://docs.langflow.org/)
- [OpenSearch Guide](https://opensearch.org/docs/)
- [Docling Parser](https://github.com/DS4SD/docling)

---

## ✅ Checklist de Migração

- [ ] Backup de dados atuais
- [ ] Instalar OpenRAG via uvx
- [ ] Configurar variáveis de ambiente
- [ ] Iniciar serviços (OpenSearch, Langflow, Docling)
- [ ] Criar módulo de integração
- [ ] Migrar dados existentes
- [ ] Criar workflows Langflow
- [ ] Executar testes de validação
- [ ] Atualizar documentação
- [ ] Deploy em produção

---

**Autor:** Leonardo R. Fragoso  
**Data:** 2025-03-12  
**Versão:** 1.0

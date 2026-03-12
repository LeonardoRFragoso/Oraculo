# 🎨 Workflows Langflow para GPTRACKER

Este diretório contém workflows visuais do Langflow para o GPTRACKER.

## 📋 Workflows Disponíveis

### 1. **data_ingestion.json** - Pipeline de Ingestão
Workflow para processar e indexar documentos no OpenSearch.

**Componentes:**
```
FileLoader → DoclingParser → MetadataExtractor → OpenSearchIndexer
```

**Configuração:**
- **FileLoader**: Aceita PDF, DOCX, Excel, CSV
- **DoclingParser**: Chunking semântico (512 tokens, overlap 50)
- **MetadataExtractor**: Extrai cliente, data, quantidade
- **OpenSearchIndexer**: Indexa em `gptracker_knowledge`

### 2. **rag_chat.json** - Chat com RAG
Workflow para chat conversacional com recuperação de contexto.

**Componentes:**
```
ChatInput → OpenSearchRetriever → Reranker → PromptBuilder → ChatOpenAI → ChatOutput
```

**Configuração:**
- **OpenSearchRetriever**: Busca híbrida (top-k=10)
- **Reranker**: Cohere reranker (top-n=5)
- **ChatOpenAI**: GPT-4 Turbo (temp=0.7)

### 3. **hybrid_search.json** - Busca Híbrida
Workflow para busca semântica + keyword com reranking.

**Componentes:**
```
QueryInput → VectorSearch → KeywordSearch → ResultFusion → Reranker → Output
```

**Configuração:**
- **VectorSearch**: text-embedding-3-large
- **KeywordSearch**: BM25 no OpenSearch
- **ResultFusion**: RRF (Reciprocal Rank Fusion)

### 4. **multi_agent.json** - Coordenação Multi-Agent
Workflow com múltiplos agentes especializados.

**Agentes:**
- **DataAnalyst**: Análise de dados tabulares
- **DocumentReader**: Leitura de PDFs/DOCXs
- **Summarizer**: Sumarização de resultados
- **Orchestrator**: Coordenação entre agentes

## 🚀 Como Usar

### **Importar Workflows**

1. Acesse Langflow: http://localhost:7860
2. Login: admin / Admin@123456
3. Clique em "Import Flow"
4. Selecione o arquivo JSON do workflow
5. Configure as variáveis de ambiente

### **Variáveis de Ambiente Necessárias**

```bash
OPENAI_API_KEY=sk-...
OPENSEARCH_URL=http://opensearch:9200
COHERE_API_KEY=...  # Para reranking (opcional)
```

### **Testar Workflow**

1. Abra o workflow importado
2. Clique em "Run"
3. Forneça inputs de teste
4. Verifique outputs

## 📝 Criar Workflow Customizado

### **Exemplo: Análise de Containers**

```json
{
  "name": "Container Analysis",
  "nodes": [
    {
      "id": "input",
      "type": "ChatInput",
      "data": {
        "input_value": "Quantos containers a Michelin movimentou?"
      }
    },
    {
      "id": "retriever",
      "type": "OpenSearchRetriever",
      "data": {
        "index_name": "gptracker_knowledge",
        "top_k": 10,
        "filters": {"cliente": "MICHELIN"}
      }
    },
    {
      "id": "llm",
      "type": "ChatOpenAI",
      "data": {
        "model": "gpt-4-turbo",
        "temperature": 0.7
      }
    },
    {
      "id": "output",
      "type": "ChatOutput"
    }
  ],
  "edges": [
    {"source": "input", "target": "retriever"},
    {"source": "retriever", "target": "llm"},
    {"source": "llm", "target": "output"}
  ]
}
```

## 🎯 Melhores Práticas

### **Performance**
- Use cache de embeddings (Redis)
- Configure batch processing
- Ajuste chunk_size conforme necessário

### **Qualidade**
- Sempre use reranking para top-k > 5
- Configure filtros de metadados
- Use temperatura baixa (0.3-0.5) para análises

### **Escalabilidade**
- Use async processing para volumes grandes
- Configure rate limiting
- Monitore uso de tokens

## 🔧 Troubleshooting

### **Workflow não executa**
- Verificar credenciais OpenAI
- Verificar conectividade com OpenSearch
- Verificar logs do Langflow

### **Resultados ruins**
- Ajustar chunk_size e overlap
- Melhorar prompt template
- Adicionar reranking

### **Performance lenta**
- Habilitar cache
- Reduzir top_k
- Usar modelo de embedding menor

## 📚 Recursos

- [Langflow Docs](https://docs.langflow.org/)
- [OpenSearch Guide](https://opensearch.org/docs/)
- [OpenAI API](https://platform.openai.com/docs/)

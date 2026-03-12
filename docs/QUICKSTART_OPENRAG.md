# 🚀 Guia de Início Rápido - OpenRAG

## ⚡ Setup em 5 Minutos

### **Pré-requisitos**
- Docker e Docker Compose instalados
- 8GB+ de RAM disponível
- 20GB+ de espaço em disco
- Chave de API da OpenAI

### **Passo 1: Clone e Configure**

```bash
cd /home/leonardo/dev/GPTracker

# Copiar arquivo de configuração
cp .env.openrag.example .env

# Editar .env e adicionar sua OPENAI_API_KEY
nano .env  # ou seu editor preferido
```

### **Passo 2: Executar Setup Automático**

```bash
# Tornar script executável (se necessário)
chmod +x scripts/setup_openrag.sh

# Executar setup
./scripts/setup_openrag.sh
```

O script irá:
- ✅ Verificar requisitos do sistema
- ✅ Configurar vm.max_map_count para OpenSearch
- ✅ Baixar imagens Docker
- ✅ Iniciar todos os serviços
- ✅ Aguardar serviços ficarem prontos

### **Passo 3: Migrar Dados Existentes**

```bash
# Executar migração
python scripts/migrate_to_openrag.py
```

A migração irá:
- 💾 Fazer backup dos dados atuais
- 📦 Migrar documentos do FAISS
- 📊 Migrar arquivos processados
- ✅ Verificar integridade

### **Passo 4: Ativar OpenRAG**

Edite o arquivo `.env` e configure:

```bash
USE_OPENRAG=true
```

### **Passo 5: Iniciar GPTRACKER**

```bash
streamlit run gptracker.py
```

---

## 🎯 Acesso aos Serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Langflow** (Workflows) | http://localhost:7860 | admin / Admin@123456 |
| **OpenSearch** (Vector Store) | http://localhost:9200 | admin / Admin@123456 |
| **OpenSearch Dashboards** | http://localhost:5601 | - |
| **Docling** (Parser) | http://localhost:5001 | - |
| **GPTRACKER** (Interface) | http://localhost:8501 | Suas credenciais |

---

## 🧪 Testar Instalação

### **Teste 1: Verificar Serviços**

```bash
# OpenSearch
curl http://localhost:9200/_cluster/health

# Langflow
curl http://localhost:7860/health

# Docling
curl http://localhost:5001/health
```

### **Teste 2: Testar Ingestão**

```python
from src.openrag_integration import OpenRAGManager
import pandas as pd

# Criar gerenciador
manager = OpenRAGManager()

# Verificar saúde
health = manager.health_check()
print(health)

# Testar com dados de exemplo
df = pd.DataFrame({
    'cliente': ['MICHELIN', 'GOODYEAR'],
    'qtd_container': [100, 50],
    'ano_mes': ['202503', '202503']
})

result = manager.ingest_dataframe(df, metadata={'source': 'test'})
print(result)
```

### **Teste 3: Testar Busca**

```python
# Buscar
results = manager.search("containers Michelin", top_k=3)
for result in results:
    print(f"Score: {result['score']:.3f} - {result['content'][:100]}")
```

### **Teste 4: Testar Chat**

```python
# Chat
response = manager.chat("Quantos containers a Michelin movimentou?")
print(response)
```

---

## 🔧 Comandos Úteis

### **Gerenciar Serviços**

```bash
# Iniciar serviços
docker-compose -f docker-compose.openrag.yml up -d

# Parar serviços
docker-compose -f docker-compose.openrag.yml down

# Ver logs
docker-compose -f docker-compose.openrag.yml logs -f

# Ver status
docker-compose -f docker-compose.openrag.yml ps

# Reiniciar serviço específico
docker-compose -f docker-compose.openrag.yml restart opensearch
```

### **Monitoramento**

```bash
# Logs do OpenSearch
docker logs gptracker-opensearch -f

# Logs do Langflow
docker logs gptracker-langflow -f

# Logs do Docling
docker logs gptracker-docling -f
```

### **Backup e Restore**

```bash
# Backup do OpenSearch
docker exec gptracker-opensearch curl -X PUT "localhost:9200/_snapshot/backup" \
  -H 'Content-Type: application/json' \
  -d '{"type": "fs", "settings": {"location": "/backups"}}'

# Criar snapshot
docker exec gptracker-opensearch curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1"

# Restaurar snapshot
docker exec gptracker-opensearch curl -X POST "localhost:9200/_snapshot/backup/snapshot_1/_restore"
```

---

## 🐛 Troubleshooting

### **Problema: OpenSearch não inicia**

```bash
# Verificar logs
docker logs gptracker-opensearch

# Solução: Aumentar vm.max_map_count
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# Reiniciar
docker-compose -f docker-compose.openrag.yml restart opensearch
```

### **Problema: Memória insuficiente**

Edite `docker-compose.openrag.yml` e reduza a memória do OpenSearch:

```yaml
environment:
  - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"  # Reduzir de 2g para 1g
```

### **Problema: Porta já em uso**

```bash
# Verificar portas em uso
sudo lsof -i :9200  # OpenSearch
sudo lsof -i :7860  # Langflow
sudo lsof -i :5601  # Dashboards

# Matar processo
sudo kill -9 <PID>
```

### **Problema: Migração lenta**

A migração pode levar tempo dependendo do volume de dados. Para acelerar:

```python
# Editar scripts/migrate_to_openrag.py
# Aumentar batch_size de 100 para 500
batch_size = 500
```

### **Problema: Langflow não conecta ao OpenSearch**

```bash
# Verificar rede Docker
docker network inspect gptracker_openrag-network

# Verificar conectividade
docker exec gptracker-langflow curl http://opensearch:9200/_cluster/health
```

---

## 📊 Monitorar Performance

### **OpenSearch Dashboards**

1. Acesse http://localhost:5601
2. Vá em "Dev Tools"
3. Execute queries:

```json
// Ver índices
GET _cat/indices?v

// Ver estatísticas do índice
GET gptracker_knowledge/_stats

// Buscar documentos
GET gptracker_knowledge/_search
{
  "query": {
    "match": {
      "content": "containers"
    }
  }
}
```

### **Métricas do Sistema**

```bash
# Uso de recursos
docker stats

# Espaço em disco
docker system df

# Limpar recursos não utilizados
docker system prune -a
```

---

## 🎨 Criar Workflows no Langflow

1. Acesse http://localhost:7860
2. Login: admin / Admin@123456
3. Criar novo workflow:
   - Clique em "New Flow"
   - Arraste componentes da barra lateral
   - Conecte os nós
   - Salve o workflow

### **Exemplo: Workflow de Ingestão**

```
FileLoader → DoclingParser → OpenSearchIndexer
```

### **Exemplo: Workflow de Chat**

```
ChatInput → OpenSearchRetriever → Reranker → ChatOpenAI → ChatOutput
```

---

## 🔐 Segurança

### **Alterar Senhas Padrão**

Edite `.env`:

```bash
OPENSEARCH_PASSWORD=SuaSenhaSegura123!
LANGFLOW_ADMIN_PASSWORD=OutraSenhaSegura456!
REDIS_PASSWORD=MaisUmaSenha789!
```

Depois reinicie os serviços:

```bash
docker-compose -f docker-compose.openrag.yml down
docker-compose -f docker-compose.openrag.yml up -d
```

### **Habilitar HTTPS**

Para produção, configure um reverse proxy (Nginx/Traefik) com SSL.

---

## 📈 Otimização de Performance

### **Cache de Embeddings**

Ative no `.env`:

```bash
ENABLE_EMBEDDING_CACHE=true
```

### **Ajustar Chunk Size**

```bash
CHUNK_SIZE=512  # Menor = mais preciso, maior = mais contexto
CHUNK_OVERLAP=50
```

### **Modelo de Embeddings**

```bash
# Mais rápido (menor qualidade)
EMBEDDING_MODEL=text-embedding-ada-002

# Melhor qualidade (mais lento)
EMBEDDING_MODEL=text-embedding-3-large
```

---

## 🆘 Suporte

- 📚 [Documentação Completa](MIGRATION_PLAN.md)
- 🐛 [Reportar Bugs](https://github.com/LeonardoRFragoso/GPTracker/issues)
- 💬 [Discussões](https://github.com/LeonardoRFragoso/GPTracker/discussions)

---

## ✅ Checklist de Validação

- [ ] Todos os serviços estão rodando (`docker-compose ps`)
- [ ] OpenSearch está saudável (`curl localhost:9200/_cluster/health`)
- [ ] Langflow está acessível (http://localhost:7860)
- [ ] Migração de dados concluída sem erros
- [ ] Busca semântica retorna resultados
- [ ] Chat RAG gera respostas coerentes
- [ ] GPTRACKER conecta ao OpenRAG (`USE_OPENRAG=true`)

---

**Pronto! Seu GPTRACKER agora está rodando com OpenRAG! 🚀**

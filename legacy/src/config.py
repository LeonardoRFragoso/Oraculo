"""
Configurações centralizadas do sistema
"""

import os

# Mapeamento de categorias e palavras-chave
CATEGORIA_MAPPING = {
    "importacao": ["importação", "importacao", "importado", "importador", "consignatário"],
    "exportacao": ["exportação", "exportacao", "exportado", "exportador"],
    "cabotagem": ["cabotagem", "costeira", "navegação costeira"]
}

# Mapeamento de colunas de cliente por tipo de operação
CLIENTE_MAPPING = {
    "importacao": [
        "CONSIGNATARIO FINAL",
        "CONSIGNATÁRIO",
        "NOME IMPORTADOR",
        "IMPORTADOR",
        "CLIENTE"
    ],
    "exportacao": [
        "NOME EXPORTADOR",
        "EXPORTADOR",
        "CLIENTE"
    ],
    "cabotagem": [
        "CLIENTE",
        "DESTINATÁRIO",
        "REMETENTE"
    ]
}

# Mapeamento de portos
PORTO_MAPPING = {
    "importacao": [
        "PORTO DE EMBARQUE",
        "PORTO EMBARQUE",
        "PORTO DE ORIGEM",
        "PORTO ORIGEM",
        "PORTO DE ORIGEM COM CÓDIGO",
        "PORTO ORIGEM COM CÓDIGO",
        "COD. PORTO EMBARQUE",
        "COD. PORTO ORIGEM",
        "PORTO DE DESCARGA",
        "PORTO DESCARGA",
        "PORTO DESCARGA COM CÓDIGO",
        "COD. PORTO DESCARGA",
        "PORTO DE DESTINO",
        "PORTO DESTINO",
        "PORTO DESTINO COM CÓDIGO",
        "COD. PORTO DESTINO",
        "PORTO"
    ],
    "exportacao": [
        "PORTO DE EMBARQUE",
        "PORTO EMBARQUE",
        "PORTO DE ORIGEM",
        "PORTO ORIGEM",
        "PORTO DE ORIGEM COM CÓDIGO",
        "PORTO ORIGEM COM CÓDIGO",
        "COD. PORTO EMBARQUE",
        "COD. PORTO ORIGEM",
        "PORTO DE DESCARGA",
        "PORTO DESCARGA",
        "PORTO DESCARGA COM CÓDIGO",
        "COD. PORTO DESCARGA",
        "PORTO DE DESTINO",
        "PORTO DESTINO",
        "PORTO DESTINO COM CÓDIGO",
        "COD. PORTO DESTINO",
        "PORTO"
    ],
    "cabotagem": [
        "PORTO DE EMBARQUE",
        "PORTO EMBARQUE",
        "PORTO DE ORIGEM",
        "PORTO ORIGEM",
        "PORTO DE ORIGEM COM CÓDIGO",
        "PORTO ORIGEM COM CÓDIGO",
        "COD. PORTO EMBARQUE",
        "COD. PORTO ORIGEM",
        "PORTO DE DESCARGA",
        "PORTO DESCARGA",
        "PORTO DESCARGA COM CÓDIGO",
        "COD. PORTO DESCARGA",
        "PORTO DE DESTINO",
        "PORTO DESTINO",
        "PORTO DESTINO COM CÓDIGO",
        "COD. PORTO DESTINO",
        "PORTO"
    ]
}

# Configuração de colunas
COLUNAS_CONFIG = {
    "quantidade": [
        "QTDE CONTAINER",
        "QTDE CONTEINER",
        "QUANTIDADE C20",
        "QUANTIDADE C40",
        "C20",
        "C40",
        "QTDE FCL",
        "TEUS",
        "VOLUMES",
        "QUANTIDADE"
    ],
    "data": [
        "DATA EMBARQUE",
        "DATA DE EMBARQUE",
        "DATA",
        "ANO/MÊS"
    ],
    "valor": [
        "VALOR FOB",
        "VALOR CIF",
        "VALOR"
    ]
}

# Configuração do Streamlit
STREAMLIT_CONFIG = {
    "page_title": "Oráculo - Análise de Dados Logísticos",
    "page_icon": "🤖",
    "layout": "wide"
}

# Configuração de cache
CACHE_CONFIG = {
    "ttl": 3600,  # Tempo de vida do cache em segundos (1 hora)
}

# Configuração da API OpenAI
OPENAI_CONFIG = {
    "model": "gpt-4-turbo",
    "temperature": 0.7,
    "max_tokens": 1000,
    "timeout": 30,
    "max_retries": 3
}

# Configuração OpenRAG
OPENRAG_CONFIG = {
    "enabled": os.getenv("USE_OPENRAG", "false").lower() == "true",
    "api_url": os.getenv("OPENRAG_API_URL", "http://localhost:7860"),
    "opensearch_url": os.getenv("OPENSEARCH_URL", "http://localhost:9200"),
    "docling_url": os.getenv("DOCLING_URL", "http://localhost:5001"),
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "index_name": os.getenv("OPENRAG_INDEX_NAME", "gptracker_knowledge"),
    "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
    "chat_model": os.getenv("CHAT_MODEL", "gpt-4-turbo"),
    "chunk_size": int(os.getenv("CHUNK_SIZE", "512")),
    "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50")),
    "chunk_strategy": os.getenv("CHUNK_STRATEGY", "semantic"),
    "enable_reranking": os.getenv("ENABLE_RERANKING", "true").lower() == "true",
    "enable_hybrid_search": os.getenv("ENABLE_HYBRID_SEARCH", "true").lower() == "true",
    "enable_cache": os.getenv("ENABLE_EMBEDDING_CACHE", "true").lower() == "true",
    "max_search_results": int(os.getenv("MAX_SEARCH_RESULTS", "10")),
    "temperature": float(os.getenv("CHAT_TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("MAX_RESPONSE_TOKENS", "1000"))
}

# Configurações para análise
ANALISE_CONFIG = {
    "metricas_principais": {
        "volume": ["qtd_container", "TEUS", "VOLUMES", "PESO BRUTO"],
        "tempo": ["DATA EMBARQUE", "ETA", "ETS", "TRANSIT-TIME"],
        "financeiro": ["VALOR FOB", "VALOR CIF"],
        "operacional": ["TIPO CARGA", "TIPO CONTEINER", "TIPO EMBARQUE"]
    },
    "agregacoes": {
        "sum": ["qtd_container", "TEUS", "VOLUMES", "PESO BRUTO"],
        "count": ["ID"],
        "unique": ["NAVIO", "VIAGEM", "ARMADOR"],
        "first": ["DATA EMBARQUE", "ETA", "ETS"]
    },
    "comparacoes_temporais": ["MoM", "YoY", "QoQ"],
    "dimensoes_analise": {
        "geografica": ["PAÍS", "PORTO", "CIDADE", "ESTADO"],
        "temporal": ["ANO/MÊS", "DATA"],
        "comercial": ["CLIENTE", "ARMADOR", "AGENTE DE CARGA"],
        "operacional": ["TIPO CARGA", "TIPO CONTEINER", "TERMINAL"]
    }
}

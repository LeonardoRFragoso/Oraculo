"""
Configurações centralizadas do sistema
"""

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
        "PORTO EMBARQUE",
        "PORTO DESCARGA",
        "PORTO ORIGEM",
        "PORTO DESTINO",
        "PORTO"
    ],
    "exportacao": [
        "PORTO DE ORIGEM",
        "PORTO EMBARQUE",
        "PORTO DESCARGA",
        "PORTO DE DESTINO",
        "PORTO"
    ],
    "cabotagem": [
        "PORTO DE DESCARGA",
        "PORTO DE DESTINO",
        "PORTO DE EMBARQUE",
        "PORTO DE ORIGEM",
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
    "ttl": 3600,  # 1 hora
    "max_entries": 100
}

# Configuração da API OpenAI
OPENAI_CONFIG = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 500,
    "timeout": 30,
    "max_retries": 3
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

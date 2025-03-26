import os
import re
import streamlit as st
import pandas as pd
import datetime
import openai
import unicodedata
from dotenv import load_dotenv
import hashlib
from pathlib import Path

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Função para normalizar texto: remove acentos e converte para minúsculas
def normalize_text(text):
    if isinstance(text, str):
        return unicodedata.normalize('NFKD', text).encode('ascii', errors='ignore').decode('utf-8').lower().strip()
    return text

# Função melhorada para limpar e converter colunas de quantidade
def limpar_qtd_coluna(coluna):
    def clean_value(val):
        if pd.isna(val):
            return 0
        if isinstance(val, (int, float)):
            return float(val)
        # Converter string para um formato padrão
        val = str(val).strip()
        val = val.replace(".", "").replace(",", ".")  # Formato brasileiro para internacional
        # Extrair primeiro número válido encontrado
        match = re.search(r'(\d+\.?\d*)', val)
        return float(match.group(1)) if match else 0

    return coluna.apply(clean_value)

# Configuração da API OpenAI usando variável de ambiente
openai.api_key = os.getenv('OPENAI_API_KEY')

# Verificação de segurança da API
if not openai.api_key:
    st.error("⚠️ Chave da API OpenAI não configurada! Por favor, configure a variável de ambiente OPENAI_API_KEY")
    st.stop()

# Mapeamento dos campos com nomes dos clientes para cada operação
MAPPING = {
    "importacao": [
        "CONSIGNATARIO FINAL",
        "CONSOLIDADOR",
        "CONSIGNATÁRIO",
        "NOME EXPORTADOR",
        "ARMADOR",
        "AGENTE INTERNACIONAL",
        "NOME IMPORTADOR",
        "AGENTE DE CARGA"
    ],
    "exportacao": [
        "NOME EXPORTADOR",
        "CONSIGNATÁRIO",
        "ARMADOR",
        "AGENTE DE CARGA"
    ],
    "cabotagem": [
        "ARMADOR",
        "DESTINATÁRIO",
        "REMETENTE"
    ]
}

# Mapeamento dos portos para cada operação, conforme as prioridades definidas
PORT_MAPPING = {
    "importacao": ["PORTO EMBARQUE", "PORTO DESCARGA", "PORTO ORIGEM", "PORTO DESTINO"],
    "exportacao": ["PORTO DE ORIGEM", "PORTO EMBARQUE", "PORTO DESCARGA", "PORTO DE DESTINO"],
    "cabotagem": ["PORTO DE DESCARGA", "PORTO DE DESTINO", "PORTO DE EMBARQUE", "PORTO DE ORIGEM"]
}

# Configurações e constantes para análise avançada
ANALISE_CONFIG = {
    "metricas_principais": {
        "volume": ["qtd_container", "TEUS", "VOLUMES", "PESO BRUTO"],
        "tempo": ["DATA EMBARQUE", "ETA", "ETS", "TRANSIT-TIME"],
        "financeiro": ["MOEDA", "PAGAMENTO"],
        "operacional": ["TIPO CARGA", "TIPO CONTEINER", "TIPO EMBARQUE"]
    },
    "agregacoes": {
        "sum": ["qtd_container", "TEUS", "VOLUMES", "PESO BRUTO"],
        "count": ["ID"],
        "unique": ["NAVIO", "VIAGEM", "ARMADOR"],
        "first": ["DATA EMBARQUE", "ETA", "ETS"]
    },
    "comparacoes_temporais": ["MoM", "YoY", "QoQ"],  # Month over Month, Year over Year, Quarter over Quarter
    "dimensoes_analise": {
        "geografica": ["PAÍS", "PORTO", "CIDADE", "ESTADO"],
        "temporal": ["ANO/MÊS", "DATA"],
        "comercial": ["cliente", "ARMADOR", "AGENTE DE CARGA"],
        "operacional": ["TIPO CARGA", "TIPO CONTEINER", "TERMINAL"]
    }
}

def analisar_tendencias(df, coluna, periodo="M"):
    """Análise de tendências temporais nos dados"""
    if "ano_mes" not in df.columns or df.empty:
        return None
    
    df = df.copy()
    df["data"] = pd.to_datetime(df["ano_mes"].astype(str), format="%Y%m")
    serie_temporal = df.groupby("data")[coluna].sum().resample(periodo).sum()
    
    # Calcular variações
    variacao = {
        "tendencia": "crescente" if serie_temporal.iloc[-1] > serie_temporal.iloc[0] else "decrescente",
        "variacao_total": ((serie_temporal.iloc[-1] / serie_temporal.iloc[0]) - 1) * 100 if serie_temporal.iloc[0] != 0 else 0,
        "media_periodo": serie_temporal.mean(),
        "pico": serie_temporal.max(),
        "vale": serie_temporal.min()
    }
    return variacao

def analisar_distribuicao(df, coluna):
    """Análise estatística da distribuição dos dados"""
    if df.empty or coluna not in df.columns:
        return None
    
    stats = {
        "media": df[coluna].mean(),
        "mediana": df[coluna].median(),
        "desvio_padrao": df[coluna].std(),
        "quartis": df[coluna].quantile([0.25, 0.5, 0.75]).to_dict(),
        "concentracao": df[coluna].value_counts().head(5).to_dict()
    }
    return stats

def gerar_insights(df, filtros):
    """Gera insights relevantes com base nos dados filtrados"""
    if df.empty:
        return []
    
    insights = []
    
    # Análise temporal
    if filtros.get("ano") or filtros.get("mes"):
        tendencias = analisar_tendencias(df, "qtd_container")
        if tendencias:
            insights.append({
                "tipo": "tendencia",
                "descricao": f"Tendência {tendencias['tendencia']} com variação de {tendencias['variacao_total']:.1f}% no período"
            })
    
    # Análise de concentração
    if filtros.get("cliente"):
        dist_portos = df.groupby("PORTO DESTINO")["qtd_container"].sum().sort_values(ascending=False)
        if not dist_portos.empty:
            principal_porto = dist_portos.index[0]
            concentracao = (dist_portos.iloc[0] / dist_portos.sum()) * 100
            insights.append({
                "tipo": "concentracao",
                "descricao": f"Principal porto de destino: {principal_porto} ({concentracao:.1f}% do volume)"
            })
    
    # Análise operacional
    tipos_container = df["TIPO CONTEINER"].value_counts()
    if not tipos_container.empty:
        insights.append({
            "tipo": "operacional",
            "descricao": f"Tipo de container mais utilizado: {tipos_container.index[0]}"
        })
    
    return insights

def interpretar_pergunta(pergunta):
    """Extrai informações relevantes da pergunta"""
    filtros = {}
    pergunta_lower = normalize_text(pergunta.lower())

    # Detecta operação
    if "export" in pergunta_lower:
        filtros["operacao"] = "exportacao"
    elif "import" in pergunta_lower:
        filtros["operacao"] = "importacao"
    elif "cabot" in pergunta_lower:
        filtros["operacao"] = "cabotagem"

    # Detecção de ano/mês
    match_ano = re.search(r'\b(20\d{2})\b', pergunta)
    if match_ano:
        filtros["ano"] = int(match_ano.group(1))
    
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }
    
    for nome, num in meses.items():
        if nome in pergunta_lower:
            filtros["mes"] = num
            break

    # Detecção de cliente
    for palavra in ["consignatario", "consignatário", "cliente", "empresa"]:
        if palavra in pergunta_lower:
            match = re.search(f"{palavra}\s+([A-Za-z0-9\s&\-\.,]+(?:\s+LTDA)?)", pergunta, flags=re.IGNORECASE)
            if match:
                filtros["cliente"] = match.group(1).strip()
                break

    return filtros

def aplicar_filtros(df, filtros):
    """Aplica os filtros ao DataFrame"""
    df_filtrado = df.copy()
    
    if filtros.get("operacao"):
        df_filtrado = df_filtrado[df_filtrado["tipo_operacao"] == filtros["operacao"]]

    if filtros.get("ano"):
        df_filtrado = df_filtrado[df_filtrado["ano_mes"].astype(str).str[:4].astype(int) == filtros["ano"]]

    if filtros.get("mes"):
        df_filtrado = df_filtrado[df_filtrado["ano_mes"].astype(str).str[-2:].astype(int) == filtros["mes"]]

    if filtros.get("cliente"):
        cliente_normalizado = normalize_text(filtros["cliente"])
        df_filtrado = df_filtrado[
            df_filtrado["cliente"].apply(lambda x: normalize_text(str(x)) if pd.notna(x) else "").str.contains(cliente_normalizado, na=False)
        ]

    return df_filtrado

def responder_consulta_local(pergunta, df):
    """Gera uma resposta baseada nos dados locais"""
    try:
        # Interpreta a pergunta e aplica filtros
        filtros = interpretar_pergunta(pergunta)
        df_filtrado = aplicar_filtros(df, filtros)
        
        if df_filtrado.empty:
            return "Nenhuma informação encontrada para os critérios especificados."
        
        # Análise básica dos dados filtrados
        total_containers = df_filtrado["qtd_container"].sum()
        num_registros = len(df_filtrado)
        
        # Prepara a resposta
        resposta = []
        
        # Cabeçalho da resposta
        if filtros.get("operacao"):
            resposta.append(f"📦 Para operação de {filtros['operacao'].upper()}:")
        else:
            resposta.append("📦 Considerando todas as operações:")
            
        # Período analisado
        if filtros.get("ano") and filtros.get("mes"):
            resposta.append(f"📅 No período: {filtros['mes']}/{filtros['ano']}")
        elif filtros.get("ano"):
            resposta.append(f"📅 No ano: {filtros['ano']}")
            
        # Cliente específico
        if filtros.get("cliente"):
            resposta.append(f"👥 Cliente: {filtros['cliente']}")
            
        # Resultados
        resposta.append(f"\n📊 Resultados:")
        resposta.append(f"- Total de containers: {total_containers:,.0f}")
        resposta.append(f"- Número de operações: {num_registros:,.0f}")
        
        # Análises adicionais
        if num_registros > 0:
            media_containers = df_filtrado["qtd_container"].mean()
            resposta.append(f"- Média de containers por operação: {media_containers:.2f}")
            
            # Top portos se houver mais de uma operação
            if num_registros > 1:
                top_portos = df_filtrado["PORTO EMBARQUE"].value_counts().head(3)
                resposta.append("\n🚢 Principais portos de embarque:")
                for porto, count in top_portos.items():
                    if pd.notna(porto):
                        resposta.append(f"- {porto}: {count:,.0f} operações")
        
        return "\n".join(resposta)
        
    except Exception as e:
        st.error(f"Erro ao processar consulta local: {str(e)}")
        return None

def responder_pergunta(pergunta, df):
    """Utiliza exclusivamente a API da OpenAI para gerar respostas contextualizadas."""
    try:
        # Prepara os dados relevantes
        filtros = interpretar_pergunta(pergunta)
        df_filtrado = aplicar_filtros(df, filtros)
        
        # Prepara o contexto para a API
        contexto = {
            "total_registros": len(df_filtrado),
            "total_containers": df_filtrado["qtd_container"].sum(),
            "media_containers": df_filtrado["qtd_container"].mean(),
            "distribuicao_portos": df_filtrado["PORTO EMBARQUE"].value_counts().head(5).to_dict(),
            "periodo": f"{filtros.get('mes', 'todos os meses')}/{filtros.get('ano', 'todos os anos')}",
            "cliente": filtros.get('cliente', 'todos os clientes'),
            "operacao": filtros.get('operacao', 'todas as operações')
        }

        # Cria um prompt detalhado para a API
        prompt = f"""Como analista especialista em logística portuária, responda à seguinte pergunta usando os dados fornecidos:

Pergunta: {pergunta}

Contexto dos Dados:
- Período analisado: {contexto['periodo']}
- Cliente: {contexto['cliente']}
- Tipo de operação: {contexto['operacao']}
- Total de registros encontrados: {contexto['total_registros']}
- Total de containers: {contexto['total_containers']:,.0f}
- Média de containers por operação: {contexto['media_containers']:.2f}

Top 5 Portos de Embarque:
{chr(10).join([f'- {porto}: {qtd:,.0f} operações' for porto, qtd in contexto['distribuicao_portos'].items()])}

Por favor, forneça uma resposta detalhada e profissional, focando especificamente nos dados solicitados na pergunta."""

        # Faz a chamada para a API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um analista especialista em logística portuária com vasta experiência em análise de dados. Suas respostas devem ser objetivas, profissionais e focadas nos dados solicitados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response['choices'][0]['message']['content']
        
    except Exception as e:
        st.error(f"Erro ao processar a pergunta: {str(e)}")
        return "Desculpe, não foi possível processar sua pergunta no momento. Por favor, tente novamente."

# --- 1. Separar múltiplos portos ---
def padronizar_dados_consolidados(df):
    """
    Padroniza os dados da planilha consolidada
    """
    df = df.copy()
    
    # Normalizar cliente com base na categoria
    colunas_cliente = {
        'importacao': ["CONSIGNATARIO FINAL", "CONSOLIDADOR", "CONSIGNATÁRIO", "NOME IMPORTADOR"],
        'exportacao': ["NOME EXPORTADOR", "CONSIGNATÁRIO"],
        'cabotagem': ["DESTINATÁRIO", "REMETENTE"]
    }
    
    # Criar coluna cliente baseada na categoria
    def get_cliente(row):
        categoria = row['tipo_operacao']
        for col in colunas_cliente.get(categoria, []):
            if col in df.columns and pd.notna(row[col]):
                return str(row[col])
        return None
    
    df['cliente'] = df.apply(get_cliente, axis=1)
    
    # Normalizar nomes de portos
    colunas_porto = [col for col in df.columns if "PORTO" in col]
    for col in colunas_porto:
        df[col] = df[col].apply(lambda x: normalize_text(str(x)) if pd.notna(x) else None)
    
    # Tratamento da coluna ANO/MÊS
    if "ANO/MÊS" in df.columns:
        df["ano_mes"] = pd.to_numeric(df["ANO/MÊS"].astype(str).str.replace(r'\D', '', regex=True), errors="coerce")
    
    # Tratamento de quantidade de containers
    def get_qtd_container(row):
        if row['tipo_operacao'] == 'cabotagem':
            qtd_c20 = limpar_qtd_coluna(pd.Series([row.get("QUANTIDADE C20", 0)])).iloc[0]
            qtd_c40 = limpar_qtd_coluna(pd.Series([row.get("QUANTIDADE C40", 0)])).iloc[0]
            return qtd_c20 + qtd_c40
        else:
            for col in ["QTDE CONTEINER", "QUANTIDADE CONTAINER"]:
                if col in df.columns and pd.notna(row[col]):
                    return limpar_qtd_coluna(pd.Series([row[col]])).iloc[0]
            # Fallback para C20 + C40
            qtd_c20 = limpar_qtd_coluna(pd.Series([row.get("C20", 0)])).iloc[0]
            qtd_c40 = limpar_qtd_coluna(pd.Series([row.get("C40", 0)])).iloc[0]
            return qtd_c20 + qtd_c40
    
    df['qtd_container'] = df.apply(get_qtd_container, axis=1)
    
    return df

@st.cache_data(ttl=3600, show_spinner=False)  # Cache por 1 hora, sem mostrar spinner do cache
def get_file_hash(file_path):
    """Calcula o hash do arquivo para detectar mudanças"""
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

@st.cache_data(ttl=3600, show_spinner=False)  # Cache por 1 hora, sem mostrar spinner do cache
def carregar_planilhas():
    """
    Carrega a planilha consolidada com todos os dados
    Usa cache do Streamlit para evitar recarregamento desnecessário
    """
    try:
        # Verifica se houve mudança no arquivo
        file_path = 'Dados_Consolidados.xlsx'
        current_hash = get_file_hash(file_path)
        
        # Se o hash mudou ou não existe no cache, recarrega os dados
        if 'file_hash' not in st.session_state or st.session_state.file_hash != current_hash:
            # Carrega a planilha consolidada
            df = pd.read_excel(file_path)
            
            # Padroniza os tipos de operação para manter compatibilidade
            categoria_mapping = {
                'Importação': 'importacao',
                'Exportação': 'exportacao',
                'Cabotagem': 'cabotagem'
            }
            
            # Mapeia a coluna Categoria para tipo_operacao
            df['tipo_operacao'] = df['Categoria'].map(categoria_mapping)
            
            # Padroniza os dados
            df = padronizar_dados_consolidados(df)
            
            # Atualiza o hash no cache
            st.session_state.file_hash = current_hash
            st.session_state.df = df
            
            # Debug: Exibe o total de registros por operação em um expander
            with st.expander("📊 Estatísticas dos Dados", expanded=False):
                st.write("Total de registros por operação:")
                st.write(df.groupby("tipo_operacao")["qtd_container"].sum())
        
        return st.session_state.df
        
    except Exception as e:
        st.error(f"Erro ao carregar a planilha consolidada: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)  # Cache por 1 hora, sem mostrar spinner do cache
def carregar_clientes():
    """Carrega e mantém em cache os dados dos clientes"""
    try:
        with open('clientes.txt', 'r', encoding='utf-8') as f:
            return [linha.strip() for linha in f.readlines()]
    except Exception as e:
        st.warning(f"Arquivo de clientes não encontrado: {e}")
        return []

# Configuração da interface do Streamlit
st.set_page_config(
    page_title="Oráculo - Análise de Dados Logísticos",
    page_icon="🤖",
    layout="wide"
)

# Interface principal
st.title("🤖 Oráculo - Análise de Dados Logísticos")

# Inicialização do estado da sessão
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.df = None
    st.session_state.file_hash = None
    st.session_state.ultima_atualizacao = None

# Carrega os dados apenas uma vez ou quando houver mudanças
if st.session_state.df is None or (
    st.session_state.ultima_atualizacao and 
    datetime.datetime.now() - st.session_state.ultima_atualizacao > datetime.timedelta(hours=1)
):
    with st.spinner("🔄 Inicializando base de dados..."):
        df = carregar_planilhas()
        st.session_state.ultima_atualizacao = datetime.datetime.now()
        
        # Exibe mensagem de sucesso apenas no carregamento inicial
        if st.session_state.df is None:
            st.success("✅ Base de dados carregada com sucesso!")
else:
    df = st.session_state.df

# Botão para forçar atualização dos dados
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🔄 Atualizar Dados"):
        with st.spinner("🔄 Recarregando dados..."):
            st.cache_data.clear()
            df = carregar_planilhas()
            st.session_state.ultima_atualizacao = datetime.datetime.now()
            st.success("✅ Dados atualizados com sucesso!")

# Dicas para formular perguntas
with st.expander("💡 Dicas para formular suas perguntas", expanded=False):
    st.markdown("""
    - Utilize o nome completo do cliente, por exemplo: 'consignatário ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA'.
    - Informe o ano (ex.: 2025) e, se necessário, o mês (por extenso, ex.: fevereiro) para filtrar os dados.
    - Especifique o tipo de operação (importação, exportação ou cabotagem) e, se for o caso, o tipo de porto (embarque, descarga, destino ou origem).
    """)

# Interface de perguntas
st.markdown("### 🔍 Faça uma pergunta sobre os dados")
pergunta = st.text_input("Digite sua pergunta:")

if pergunta:
    with st.spinner("🤔 Analisando sua pergunta..."):
        resposta = responder_pergunta(pergunta, df)
        st.markdown("### 📝 Resposta")
        st.write(resposta)

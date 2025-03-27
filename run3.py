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
import json
import time

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

# Nova função para unificar contagem de containers considerando tipos de operação
def unificar_contagem_containers(df):
    """
    Unifica a contagem de containers considerando diferentes campos
    """
    df = df.copy()
    
    # Inicializar coluna de quantidade total de containers
    df['qtd_container'] = 0
    
    # Lista de todas as possíveis colunas de quantidade
    colunas_quantidade = [
        'QTDE CONTAINER', 'QTDE CONTEINER', 'QUANTIDADE C20', 'QUANTIDADE C40',
        'C20', 'C40', 'QTDE FCL', 'TEUS'
    ]
    
    # Converter e somar todas as colunas de quantidade disponíveis
    for col in colunas_quantidade:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    # Somar C20 e C40 se existirem
    if 'C20' in df.columns:
        df['qtd_container'] += df['C20']
    if 'C40' in df.columns:
        df['qtd_container'] += df['C40']
    
    # Somar QUANTIDADE C20 e QUANTIDADE C40 se existirem
    if 'QUANTIDADE C20' in df.columns:
        df['qtd_container'] += df['QUANTIDADE C20']
    if 'QUANTIDADE C40' in df.columns:
        df['qtd_container'] += df['QUANTIDADE C40']
    
    # Se ainda não há quantidade, tentar QTDE CONTAINER ou QTDE CONTEINER
    if df['qtd_container'].sum() == 0:
        if 'QTDE CONTAINER' in df.columns:
            df['qtd_container'] = df['QTDE CONTAINER']
        elif 'QTDE CONTEINER' in df.columns:
            df['qtd_container'] = df['QTDE CONTEINER']
        elif 'QTDE FCL' in df.columns:
            df['qtd_container'] = df['QTDE FCL']
        elif 'TEUS' in df.columns:
            df['qtd_container'] = df['TEUS']
    
    return df

# Função melhorada para padronizar datas
def padronizar_datas(df):
    """
    Padroniza as datas em diferentes formatos e cria colunas de ano e mês
    """
    # Lista de possíveis colunas de data
    data_cols = ['DATA EMBARQUE', 'DATA DE EMBARQUE']
    
    data_padronizada = False
    for col in data_cols:
        if col in df.columns:
            try:
                df['data_embarque_padronizada'] = pd.to_datetime(df[col], errors='coerce')
                data_padronizada = True
                break
            except:
                continue
    
    # Se conseguimos padronizar alguma data
    if data_padronizada:
        df['ano'] = df['data_embarque_padronizada'].dt.year
        df['mes'] = df['data_embarque_padronizada'].dt.month
        df['ano_mes'] = df['ano'] * 100 + df['mes']
    # Se não conseguimos, tentar usar ANO/MÊS
    elif 'ANO/MÊS' in df.columns:
        df['ANO/MÊS'] = pd.to_numeric(df['ANO/MÊS'], errors='coerce').fillna(0)
        df['ano'] = df['ANO/MÊS'] // 100
        df['mes'] = df['ANO/MÊS'] % 100
        df['ano_mes'] = df['ANO/MÊS']
    
    return df

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
    
    # Detectar operação
    operacoes = {
        "importacao": ["importa", "import", "importação", "importado", "importados"],
        "exportacao": ["exporta", "export", "exportação", "exportado", "exportados"],
        "cabotagem": ["cabot", "cabotagem"]
    }
    
    for operacao, palavras_chave in operacoes.items():
        if any(palavra in pergunta_lower for palavra in palavras_chave):
            filtros["operacao"] = operacao
            break
    
    # Detectar ano/mês
    # Procura por padrões como "2023", "ano de 2023", "em 2023"
    padrao_ano = r'\b(?:(?:ano|em|de)\s+)?20\d{2}\b'
    match_ano = re.search(padrao_ano, pergunta)
    if match_ano:
        ano = re.search(r'20\d{2}', match_ano.group())
        if ano:
            filtros["ano"] = int(ano.group())
    
    # Mapeamento de meses incluindo variações comuns
    meses = {
        1: ["janeiro", "jan"],
        2: ["fevereiro", "fev"],
        3: ["março", "marco", "mar"],
        4: ["abril", "abr"],
        5: ["maio", "mai"],
        6: ["junho", "jun"],
        7: ["julho", "jul"],
        8: ["agosto", "ago"],
        9: ["setembro", "set"],
        10: ["outubro", "out"],
        11: ["novembro", "nov"],
        12: ["dezembro", "dez"]
    }
    
    # Procura por mês na pergunta
    for num, variantes in meses.items():
        if any(mes in pergunta_lower for mes in variantes):
            filtros["mes"] = num
            break
    
    # Detectar porto
    portos_variantes = {
        "RIO DE JANEIRO": ["rio", "rio de janeiro", "rj", "porto do rio"],
        "SANTOS": ["santos", "porto de santos", "sp"],
        "PARANAGUA": ["paranagua", "paranaguá", "porto de paranaguá", "pr"],
        "ITAJAI": ["itajai", "itajaí", "porto de itajaí", "sc"],
        "VITORIA": ["vitoria", "vitória", "porto de vitória", "es"],
        "MANAUS": ["manaus", "porto de manaus", "am"],
        "ITAGUAI": ["itaguai", "itaguaí", "porto de itaguaí", "sepetiba", "rj"],
        "SUAPE": ["suape", "porto de suape", "pe"],
        "PECEM": ["pecem", "pecém", "porto do pecém", "ce"],
        "SALVADOR": ["salvador", "porto de salvador", "ba"]
    }
    
    for porto, variantes in portos_variantes.items():
        if any(var in pergunta_lower for var in variantes):
            filtros["porto"] = porto
            break
    
    return filtros

def aplicar_filtros(df, filtros):
    """Aplica filtros ao DataFrame"""
    if df.empty:
        return df
    
    df_filtrado = df.copy()
    
    # Filtro por ano
    if "ano" in filtros and filtros["ano"]:
        if "ANO/MÊS" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["ANO/MÊS"].astype(str).str[:4].astype(int) == filtros["ano"]]
    
    # Filtro por mês
    if "mes" in filtros and filtros["mes"]:
        if "ANO/MÊS" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["ANO/MÊS"].astype(str).str[4:].astype(int) == filtros["mes"]]
    
    # Filtro por tipo de operação
    if "operacao" in filtros and filtros["operacao"]:
        if "Categoria" in df_filtrado.columns:
            categoria_map = {
                "importacao": "Importação",
                "exportacao": "Exportação",
                "cabotagem": "Cabotagem"
            }
            categoria = categoria_map.get(filtros["operacao"])
            if categoria:
                df_filtrado = df_filtrado[df_filtrado["Categoria"] == categoria]
    
    # Filtro por porto
    if "porto" in filtros and filtros["porto"]:
        porto = filtros["porto"]
        colunas_porto = [
            "PORTO DE DESCARGA", "PORTO DESCARGA", "PORTO DE DESTINO", "PORTO DESTINO",
            "PORTO DE EMBARQUE", "PORTO EMBARQUE", "PORTO DE ORIGEM", "PORTO ORIGEM"
        ]
        
        mascara_porto = pd.Series(False, index=df_filtrado.index)
        for col in colunas_porto:
            if col in df_filtrado.columns:
                mascara_porto = mascara_porto | df_filtrado[col].str.contains(porto, case=False, na=False)
        df_filtrado = df_filtrado[mascara_porto]
    
    return df_filtrado

def prepare_context(df, filtros, max_tokens=3000):
    """Prepara o contexto dos dados para a API"""
    if df.empty:
        return "Não foram encontrados dados para os filtros especificados."
    
    # Identificar colunas relevantes para análise
    colunas_cliente = {
        'importacao': ["CONSIGNATARIO FINAL", "NOME IMPORTADOR", "CONSIGNATÁRIO"],
        'exportacao': ["NOME EXPORTADOR"],
        'cabotagem': ["DESTINATÁRIO", "REMETENTE"]
    }
    
    # Determinar colunas de cliente com base na operação
    if "operacao" in filtros:
        cols_cliente = colunas_cliente.get(filtros["operacao"], [])
    else:
        cols_cliente = [col for cols in colunas_cliente.values() for col in cols]
    
    # Filtrar apenas colunas existentes
    cols_cliente = [col for col in cols_cliente if col in df.columns]
    
    # Agregação por cliente
    resultados = []
    if cols_cliente:
        for col in cols_cliente:
            if col in df.columns:
                agg = df.groupby(col)["qtd_container"].sum().sort_values(ascending=False)
                for cliente, total in agg.items():
                    if pd.notna(cliente) and cliente != "":
                        resultados.append((cliente, total))
    
    # Ordenar resultados por quantidade total
    resultados.sort(key=lambda x: x[1], reverse=True)
    
    # Preparar contexto
    contexto = []
    
    # Adicionar informações dos filtros
    if "operacao" in filtros:
        contexto.append(f"Operação: {filtros['operacao']}")
    if "ano" in filtros:
        contexto.append(f"Ano: {filtros['ano']}")
    if "mes" in filtros:
        contexto.append(f"Mês: {filtros['mes']}")
    if "porto" in filtros:
        contexto.append(f"Porto: {filtros['porto']}")
    
    # Adicionar total geral
    total_containers = df["qtd_container"].sum()
    contexto.append(f"\nTotal de containers: {total_containers:.0f}")
    
    # Adicionar resultados por cliente
    if resultados:
        contexto.append("\nResultados por cliente:")
        for cliente, total in resultados[:5]:  # Top 5 clientes
            contexto.append(f"- {cliente}: {total:.0f} containers")
    
    return "\n".join(contexto)

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

def responder_pergunta(pergunta, df, max_retries=3, timeout=30):
    """Utiliza a API da OpenAI para gerar respostas contextualizadas"""
    try:
        # Extrair informações da pergunta
        filtros = interpretar_pergunta(pergunta)
        
        # Aplicar filtros aos dados
        df_filtrado = aplicar_filtros(df, filtros)
        
        # Se não há dados após a filtragem
        if df_filtrado.empty:
            return "Não foram encontrados dados que correspondam aos critérios da pergunta."
        
        # Preparar o contexto com os dados filtrados
        contexto = prepare_context(df_filtrado, filtros)
        
        # Preparar o prompt para a API
        prompt = f"""Com base nos dados fornecidos abaixo, responda à pergunta: "{pergunta}"

Contexto dos dados:
{contexto}

Por favor, forneça uma resposta clara e direta, incluindo números específicos quando relevante."""
        
        # Configurar a chamada à API
        messages = [
            {"role": "system", "content": "Você é um assistente especializado em análise de dados logísticos. Forneça respostas precisas e diretas, incluindo números específicos quando disponíveis."},
            {"role": "user", "content": prompt}
        ]
        
        # Fazer a chamada à API com retry
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.5,
                    max_tokens=500,
                    timeout=timeout
                )
                
                # Extrair e retornar a resposta
                resposta = response.choices[0].message.content.strip()
                return resposta
                
            except openai.error.RateLimitError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except openai.error.APIError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
        
    except Exception as e:
        st.error(f"Erro ao processar sua pergunta: {str(e)}")
        return "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente."

def padronizar_dados_consolidados(df):
    """
    Padroniza os dados da planilha consolidada
    """
    df = df.copy()
    
    # Mapeamento de colunas por tipo de operação
    colunas_cliente = {
        'importacao': {
            'cliente': ['CONSIGNATARIO FINAL', 'NOME IMPORTADOR', 'CONSIGNATÁRIO'],
            'porto': ['PORTO DE DESCARGA', 'PORTO DESCARGA', 'PORTO DE DESTINO', 'PORTO DESTINO']
        },
        'exportacao': {
            'cliente': ['NOME EXPORTADOR'],
            'porto': ['PORTO DE EMBARQUE', 'PORTO EMBARQUE']
        },
        'cabotagem': {
            'cliente': ['DESTINATÁRIO', 'REMETENTE'],
            'porto': ['PORTO DE ORIGEM', 'PORTO ORIGEM', 'PORTO DE DESTINO', 'PORTO DESTINO']
        }
    }
    
    # Criar coluna de tipo_operacao baseada na Categoria
    categoria_mapping = {
        'Importação': 'importacao',
        'Exportação': 'exportacao',
        'Cabotagem': 'cabotagem'
    }
    df['tipo_operacao'] = df['Categoria'].map(categoria_mapping)
    
    # Processar ANO/MÊS
    if 'ANO/MÊS' in df.columns:
        df['ANO/MÊS'] = pd.to_numeric(df['ANO/MÊS'].astype(str), errors='coerce')
        df['ano'] = df['ANO/MÊS'].astype(str).str[:4].astype(int)
        df['mes'] = df['ANO/MÊS'].astype(str).str[4:].astype(int)

    # Normalizar nomes de portos
    colunas_porto = [
        'PORTO DE DESCARGA', 'PORTO DESCARGA', 'PORTO DE DESTINO', 'PORTO DESTINO',
        'PORTO DE EMBARQUE', 'PORTO EMBARQUE', 'PORTO DE ORIGEM', 'PORTO ORIGEM'
    ]
    
    for col in colunas_porto:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: normalize_text(str(x)) if pd.notna(x) else None)
    
    # Unificar contagem de containers
    df = unificar_contagem_containers(df)
    
    return df

@st.cache_data(ttl=3600, show_spinner=False)
def get_file_hash(file_path):
    """Calcula o hash do arquivo para detectar mudanças"""
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_planilhas():
    """
    Carrega a planilha consolidada com todos os dados
    Usa cache do Streamlit para evitar recarregamento desnecessário
    """
    try:
        # Verificar se o arquivo existe
        file_path = 'Dados_Consolidados.xlsx'
        if not os.path.exists(file_path):
            st.error(f"Arquivo não encontrado: {file_path}")
            return pd.DataFrame()

        # Carregar o arquivo
        df = pd.read_excel(file_path)
        
        # Verificar se há dados
        if df.empty:
            st.error("A planilha está vazia")
            return df

        # Padronizar os dados
        df = padronizar_dados_consolidados(df)
        
        # Criar coluna de tipo_operacao baseada na Categoria
        categoria_mapping = {
            'Importação': 'importacao',
            'Exportação': 'exportacao',
            'Cabotagem': 'cabotagem'
        }
        df['tipo_operacao'] = df['Categoria'].map(categoria_mapping)

        # Unificar contagem de containers
        df = unificar_contagem_containers(df)
        
        # Padronizar datas
        df = padronizar_datas(df)
        
        # Criar colunas de ano e mês a partir de ANO/MÊS se existir
        if 'ANO/MÊS' in df.columns:
            df['ano'] = df['ANO/MÊS'].astype(str).str[:4].astype(int)
            df['mes'] = df['ANO/MÊS'].astype(str).str[4:].astype(int)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
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

"""
Aplicação principal do Oráculo - Análise de Dados Logísticos
"""
import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Carregar variáveis de ambiente
load_dotenv()

# Verificar chave da API
if not os.getenv('OPENAI_API_KEY'):
    st.error("⚠️ Chave da API OpenAI não configurada! Configure a variável de ambiente OPENAI_API_KEY")
    st.stop()

# Importar módulos do projeto
from src.data_loader import carregar_planilhas
from src.query_interpreter import interpretar_pergunta
from src.api_response import responder_pergunta
from src.data_processing import processar_dados

# Configurar página
st.set_page_config(
    page_title="Oráculo - Análise de Dados Logísticos",
    page_icon="🤖",
    layout="wide"
)

# Título da aplicação
st.title("🤖 Oráculo - Análise de Dados Logísticos")

# Botão para atualizar dados
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.success("Cache limpo! Os dados serão recarregados na próxima consulta.")

# Carregar e processar dados
@st.cache_data(ttl=3600)
def carregar_dados():
    """Carrega e processa os dados das planilhas"""
    df = carregar_planilhas()
    if not df.empty:
        df = processar_dados(df)
    return df

# Interface para perguntas
with st.expander("💡 Dicas para formular suas perguntas", expanded=True):
    st.markdown("""
    Você pode perguntar sobre:
    - Volume de containers por período
    - Principais clientes e portos
    - Comparações entre períodos
    - Análises de tendências
    - Informações específicas por cliente
    """)

# Campo de entrada para a pergunta
pergunta = st.text_input("Digite sua pergunta:", placeholder="Faça uma pergunta sobre os dados")

if pergunta:
    try:
        # Carregar dados
        df = carregar_dados()
        
        if df.empty:
            st.error("Não foi possível carregar os dados. Verifique se as planilhas estão na pasta 'dados'.")
        else:
            # Interpretar a pergunta e extrair filtros
            filtros = interpretar_pergunta(pergunta, df)
            
            # Obter resposta
            with st.spinner("Analisando dados..."):
                resposta = responder_pergunta(pergunta, df, filtros)
            
            # Exibir resposta
            st.markdown("📝 Resposta")
            st.write(resposta)
            
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar sua pergunta: {str(e)}")
        st.error("Por favor, tente reformular sua pergunta ou entre em contato com o suporte.")

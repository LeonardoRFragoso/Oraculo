"""
Aplicativo principal do Oráculo - Análise de Dados Logísticos
"""
import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from src.data_loader import carregar_planilhas
from src.query_interpreter import interpretar_pergunta
from src.api_response import responder_pergunta
from src.data_processing import processar_dados

def main():
    # Carregar variáveis de ambiente
    load_dotenv()

    # Verificar chave da API
    if not os.getenv('OPENAI_API_KEY'):
        st.error("⚠️ Chave da API OpenAI não configurada! Configure a variável de ambiente OPENAI_API_KEY")
        st.stop()

    # Configurar página
    st.set_page_config(
        page_title="Oráculo - Análise de Dados Logísticos",
        page_icon="📊",
        layout="wide"
    )
    
    # Título do aplicativo
    st.title("📊 Oráculo - Análise de Dados Logísticos")
    
    # Botão para atualizar dados
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.success("Cache limpo! Os dados serão recarregados na próxima consulta.")
    
    # Carregar dados
    try:
        df = carregar_planilhas()
        if not df.empty:
            df = processar_dados(df)
        if df.empty:
            st.error("Não foi possível carregar os dados. Verifique se os arquivos existem na pasta 'dados'.")
            return
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return
    
    # Seção de dicas
    with st.expander("💡 Dicas para formular suas perguntas"):
        st.write("Você pode perguntar sobre:")
        st.write("- Volume de containers por período")
        st.write("- Principais clientes e portos")
        st.write("- Comparações entre períodos")
        st.write("- Análises de tendências")
        st.write("- Informações específicas por cliente")
    
    # Campo de pergunta
    pergunta = st.text_input("Digite sua pergunta:")
    
    if pergunta:
        try:
            with st.spinner("Processando sua pergunta..."):
                # Interpretar a pergunta e extrair filtros
                filtros = interpretar_pergunta(pergunta, df)
                
                if not filtros:
                    st.error("Não foi possível interpretar sua pergunta. Por favor, tente reformular.")
                    return
                
                # Gerar resposta
                tipo_analise = filtros.get('tipo_analise', 'total')
                resposta = responder_pergunta(df, tipo_analise, filtros)
                
                # Exibir resposta
                st.write("📝 Resposta")
                st.write(resposta)
                
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar sua pergunta. Por favor, tente reformular ou entre em contato com o suporte. Detalhes: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        if os.environ.get('DEBUG'):
            st.exception(e)

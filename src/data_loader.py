"""
Módulo responsável pelo carregamento e cache de dados
"""
import os
import pandas as pd
import streamlit as st
from pathlib import Path
from .config import CACHE_CONFIG

@st.cache_data(ttl=CACHE_CONFIG['ttl'])
def carregar_planilhas(nome_arquivo='Dados_Consolidados.xlsx'):
    """Carrega dados das planilhas Excel"""
    try:
        # Obter caminho absoluto do diretório de dados
        diretorio_dados = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dados')
        caminho_arquivo = os.path.join(diretorio_dados, nome_arquivo)
        
        print(f"Tentando carregar arquivo: {caminho_arquivo}")
        
        if not os.path.exists(caminho_arquivo):
            print(f"Arquivo não encontrado: {caminho_arquivo}")
            st.error(f"Arquivo não encontrado: {nome_arquivo}")
            return pd.DataFrame()
        
        # Carregar dados do Excel
        df = pd.read_excel(caminho_arquivo)
        
        if df.empty:
            st.warning("A planilha está vazia.")
            return pd.DataFrame()
            
        print(f"Dados carregados com sucesso. Shape: {df.shape}")
        return df
        
    except Exception as e:
        print(f"Erro ao carregar planilhas: {str(e)}")
        st.error(f"Erro ao carregar a planilha: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_CONFIG['ttl'])
def carregar_clientes():
    """Carrega dados dos clientes"""
    try:
        # Obter caminho absoluto do diretório de dados
        diretorio_dados = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dados')
        caminho_arquivo = os.path.join(diretorio_dados, 'Clientes.xlsx')
        
        print(f"Tentando carregar arquivo de clientes: {caminho_arquivo}")
        
        if not os.path.exists(caminho_arquivo):
            print(f"Arquivo de clientes não encontrado: {caminho_arquivo}")
            st.error("Arquivo de clientes não encontrado.")
            return pd.DataFrame()
        
        # Carregar dados do Excel
        df_clientes = pd.read_excel(caminho_arquivo)
        
        if df_clientes.empty:
            st.warning("A planilha de clientes está vazia.")
            return pd.DataFrame()
            
        print(f"Dados de clientes carregados com sucesso. Shape: {df_clientes.shape}")
        return df_clientes
        
    except Exception as e:
        print(f"Erro ao carregar dados dos clientes: {str(e)}")
        st.error(f"Erro ao carregar dados dos clientes: {str(e)}")
        return pd.DataFrame()

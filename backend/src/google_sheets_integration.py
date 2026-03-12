"""
Módulo de Integração com Google Sheets
Permite carregar dados diretamente de planilhas do Google Sheets via URL
"""

import pandas as pd
import gspread
from google.auth import default
from google.oauth2.service_account import Credentials
import streamlit as st
import re
import logging
from typing import Optional, Dict, List, Tuple
import json
import os
from datetime import datetime

class GoogleSheetsIntegrator:
    def __init__(self):
        self.gc = None
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def authenticate_service_account(self, credentials_path: str = None) -> bool:
        """
        Autenticar usando Service Account (método recomendado para produção)
        """
        try:
            if credentials_path and os.path.exists(credentials_path):
                # Usar arquivo de credenciais específico
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                self.gc = gspread.authorize(creds)
                self.logger.info("Autenticação com Service Account realizada com sucesso")
                return True
            else:
                self.logger.warning("Arquivo de credenciais não encontrado")
                return False
        except Exception as e:
            self.logger.error(f"Erro na autenticação: {str(e)}")
            return False
    
    def authenticate_oauth(self) -> bool:
        """
        Autenticar usando OAuth (método para desenvolvimento)
        """
        try:
            # Tentar usar credenciais padrão do ambiente
            creds, _ = default()
            self.gc = gspread.authorize(creds)
            self.logger.info("Autenticação OAuth realizada com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro na autenticação OAuth: {str(e)}")
            return False
    
    def extract_sheet_id_and_gid(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrair Sheet ID e GID da URL do Google Sheets
        """
        try:
            # Padrão para extrair sheet_id
            sheet_id_pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            sheet_id_match = re.search(sheet_id_pattern, url)
            
            # Padrão para extrair gid (aba específica)
            gid_pattern = r'[#&]gid=([0-9]+)'
            gid_match = re.search(gid_pattern, url)
            
            sheet_id = sheet_id_match.group(1) if sheet_id_match else None
            gid = gid_match.group(1) if gid_match else None
            
            return sheet_id, gid
        except Exception as e:
            self.logger.error(f"Erro ao extrair IDs da URL: {str(e)}")
            return None, None
    
    def load_sheet_data(self, url: str, sheet_name: str = None) -> Optional[pd.DataFrame]:
        """
        Carregar dados de uma planilha do Google Sheets
        """
        try:
            if not self.gc:
                st.error("Não foi possível autenticar com Google Sheets")
                return None
            
            sheet_id, gid = self.extract_sheet_id_and_gid(url)
            if not sheet_id:
                st.error("URL inválida do Google Sheets")
                return None
            
            # Abrir a planilha
            spreadsheet = self.gc.open_by_key(sheet_id)
            
            # Selecionar a aba
            if gid:
                # Buscar worksheet por GID
                worksheet = None
                for ws in spreadsheet.worksheets():
                    if str(ws.id) == gid:
                        worksheet = ws
                        break
                if not worksheet:
                    st.error(f"Aba com GID {gid} não encontrada")
                    return None
            elif sheet_name:
                worksheet = spreadsheet.worksheet(sheet_name)
            else:
                worksheet = spreadsheet.sheet1
            
            # Obter todos os dados
            data = worksheet.get_all_records()
            
            if not data:
                st.warning("Planilha vazia ou sem dados")
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(data)
            
            # Limpar dados vazios
            df = df.dropna(how='all')  # Remover linhas completamente vazias
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remover colunas unnamed
            
            self.logger.info(f"Dados carregados com sucesso: {len(df)} linhas, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados da planilha: {str(e)}")
            st.error(f"Erro ao carregar planilha: {str(e)}")
            return None
    
    def get_sheet_info(self, url: str) -> Optional[Dict]:
        """
        Obter informações sobre a planilha (abas disponíveis, etc.)
        """
        try:
            if not self.gc:
                return None
            
            sheet_id, _ = self.extract_sheet_id_and_gid(url)
            if not sheet_id:
                return None
            
            spreadsheet = self.gc.open_by_key(sheet_id)
            
            info = {
                'title': spreadsheet.title,
                'sheets': []
            }
            
            for worksheet in spreadsheet.worksheets():
                sheet_info = {
                    'name': worksheet.title,
                    'id': worksheet.id,
                    'rows': worksheet.row_count,
                    'cols': worksheet.col_count
                }
                info['sheets'].append(sheet_info)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações da planilha: {str(e)}")
            return None
    
    def validate_sheet_access(self, url: str) -> bool:
        """
        Validar se a planilha está acessível
        """
        try:
            if not self.gc:
                return False
            
            sheet_id, _ = self.extract_sheet_id_and_gid(url)
            if not sheet_id:
                return False
            
            # Tentar abrir a planilha
            spreadsheet = self.gc.open_by_key(sheet_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Planilha não acessível: {str(e)}")
            return False

class GoogleSheetsUI:
    """Interface do usuário para integração com Google Sheets"""
    
    def __init__(self):
        self.integrator = GoogleSheetsIntegrator()
        
    def setup_authentication(self):
        """Configurar autenticação no Streamlit"""
        st.subheader("🔐 Configuração de Autenticação Google Sheets")
        
        auth_method = st.radio(
            "Método de Autenticação:",
            ["Service Account (Recomendado)", "OAuth (Desenvolvimento)"]
        )
        
        if auth_method == "Service Account (Recomendado)":
            st.info("""
            **Para usar Service Account:**
            1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
            2. Crie um projeto ou selecione um existente
            3. Ative a API do Google Sheets e Google Drive
            4. Crie uma Service Account
            5. Baixe o arquivo JSON de credenciais
            6. Faça upload do arquivo abaixo
            """)
            
            uploaded_file = st.file_uploader(
                "Upload do arquivo de credenciais JSON",
                type=['json'],
                help="Arquivo JSON baixado do Google Cloud Console"
            )
            
            if uploaded_file:
                # Salvar arquivo temporariamente
                credentials_path = "temp_credentials.json"
                with open(credentials_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if st.button("Autenticar"):
                    if self.integrator.authenticate_service_account(credentials_path):
                        st.success("✅ Autenticação realizada com sucesso!")
                        st.session_state['google_sheets_authenticated'] = True
                        # Remover arquivo temporário
                        os.remove(credentials_path)
                    else:
                        st.error("❌ Falha na autenticação")
                        if os.path.exists(credentials_path):
                            os.remove(credentials_path)
        
        else:  # OAuth
            st.warning("OAuth requer configuração adicional no ambiente")
            if st.button("Tentar Autenticação OAuth"):
                if self.integrator.authenticate_oauth():
                    st.success("✅ Autenticação OAuth realizada com sucesso!")
                    st.session_state['google_sheets_authenticated'] = True
                else:
                    st.error("❌ Falha na autenticação OAuth")
    
    def load_sheet_interface(self):
        """Interface para carregar planilhas"""
        if not st.session_state.get('google_sheets_authenticated', False):
            st.warning("⚠️ Autenticação necessária para carregar planilhas")
            return None
        
        st.subheader("📊 Carregar Planilha do Google Sheets")
        
        # URLs das planilhas mencionadas pelo usuário
        predefined_sheets = {
            "Budget Mensal por Empresa": "https://docs.google.com/spreadsheets/d/1R1ntD_FotSEQX7fLJ20yudEuGxuFkun9/edit?gid=757859154#gid=757859154",
            "Comparativo e Oportunidades": "https://docs.google.com/spreadsheets/d/1Bphi7lChPqh12kAStpupXJmCbwcdImKo/edit?gid=251726202#gid=251726202"
        }
        
        sheet_option = st.selectbox(
            "Escolha uma planilha:",
            ["Selecione...", "Budget Mensal por Empresa", "Comparativo e Oportunidades", "URL Personalizada"]
        )
        
        url = ""
        if sheet_option in predefined_sheets:
            url = predefined_sheets[sheet_option]
            st.info(f"URL selecionada: {url}")
        elif sheet_option == "URL Personalizada":
            url = st.text_input(
                "Cole a URL da planilha do Google Sheets:",
                placeholder="https://docs.google.com/spreadsheets/d/..."
            )
        
        if url and st.button("Carregar Planilha"):
            with st.spinner("Carregando dados da planilha..."):
                # Validar acesso
                if not self.integrator.validate_sheet_access(url):
                    st.error("❌ Não foi possível acessar a planilha. Verifique se ela está compartilhada publicamente ou com a service account.")
                    return None
                
                # Obter informações da planilha
                sheet_info = self.integrator.get_sheet_info(url)
                if sheet_info:
                    st.success(f"✅ Planilha encontrada: **{sheet_info['title']}**")
                    
                    # Mostrar abas disponíveis
                    if len(sheet_info['sheets']) > 1:
                        st.info("Abas disponíveis:")
                        for sheet in sheet_info['sheets']:
                            st.write(f"- {sheet['name']} (ID: {sheet['id']}) - {sheet['rows']} linhas")
                
                # Carregar dados
                df = self.integrator.load_sheet_data(url)
                
                if df is not None:
                    st.success(f"✅ Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
                    
                    # Mostrar preview dos dados
                    st.subheader("📋 Preview dos Dados")
                    st.dataframe(df.head(10))
                    
                    # Mostrar informações das colunas
                    st.subheader("📊 Informações das Colunas")
                    col_info = pd.DataFrame({
                        'Coluna': df.columns,
                        'Tipo': df.dtypes,
                        'Não Nulos': df.count(),
                        'Exemplo': [str(df[col].iloc[0]) if len(df) > 0 else 'N/A' for col in df.columns]
                    })
                    st.dataframe(col_info)
                    
                    # Salvar dados na sessão para uso posterior
                    st.session_state[f'google_sheet_data_{sheet_option}'] = df
                    
                    # Opção de salvar localmente
                    if st.button("💾 Salvar Dados Localmente"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"dados/google_sheet_{sheet_option.lower().replace(' ', '_')}_{timestamp}.xlsx"
                        
                        # Criar diretório se não existir
                        os.makedirs(os.path.dirname(filename), exist_ok=True)
                        
                        df.to_excel(filename, index=False)
                        st.success(f"✅ Dados salvos em: {filename}")
                    
                    return df
        
        return None
    
    def render_integration_page(self):
        """Renderizar página completa de integração"""
        st.title("🔗 Integração Google Sheets")
        
        # Verificar se já está autenticado
        if not st.session_state.get('google_sheets_authenticated', False):
            self.setup_authentication()
        else:
            st.success("✅ Autenticado com Google Sheets")
            
            # Interface para carregar planilhas
            df = self.load_sheet_interface()
            
            # Botão para desautenticar
            if st.button("🔓 Desconectar"):
                st.session_state['google_sheets_authenticated'] = False
                st.rerun()
        
        # Instruções adicionais
        with st.expander("📖 Instruções de Uso"):
            st.markdown("""
            ### Como usar a integração com Google Sheets:
            
            1. **Autenticação**: Configure as credenciais do Google Cloud
            2. **Compartilhamento**: Certifique-se de que a planilha está:
               - Compartilhada publicamente (para leitura), OU
               - Compartilhada com o email da service account
            3. **URL**: Use a URL completa da planilha, incluindo o GID da aba se necessário
            4. **Dados**: Os dados serão carregados automaticamente e estarão disponíveis para análise
            
            ### Formatos de URL suportados:
            - `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
            - `https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=GID_NUMBER`
            
            ### Tipos de dados detectados automaticamente:
            - Dados logísticos (containers, clientes, períodos)
            - Dados comerciais (receita, vendas, metas)
            - Dados de budget (metas, realizações)
            - Dados de oportunidades (prospects, probabilidades)
            """)

def create_google_sheets_integration():
    """Função para criar a interface de integração"""
    ui = GoogleSheetsUI()
    return ui.render_integration_page()

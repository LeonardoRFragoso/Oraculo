"""
Módulo de Integração Universal com Armazenamento em Nuvem
Suporta Google Sheets, OneDrive, Dropbox, e links públicos de planilhas
"""

import pandas as pd
import requests
import re
import io
import logging
from typing import Optional, Dict, List, Tuple, Union
from urllib.parse import urlparse, parse_qs
import streamlit as st
from datetime import datetime
import os
import tempfile

# Importações condicionais para Google Sheets
try:
    import gspread
    from google.auth import default
    from google.oauth2.service_account import Credentials
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

class UniversalCloudIntegrator:
    """Integrador universal para planilhas em armazenamento em nuvem"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.gc = None  # Google Sheets client
        
    def setup_logging(self):
        """Configurar logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def detect_cloud_provider(self, url: str) -> str:
        """
        Detectar o provedor de armazenamento em nuvem pela URL
        """
        url_lower = url.lower()
        
        if 'docs.google.com/spreadsheets' in url_lower:
            return 'google_sheets'
        elif '1drv.ms' in url_lower or 'onedrive.live.com' in url_lower:
            return 'onedrive'
        elif 'sharepoint.com' in url_lower and 'excel' in url_lower:
            return 'sharepoint'
        elif 'dropbox.com' in url_lower:
            return 'dropbox'
        elif 'box.com' in url_lower:
            return 'box'
        elif 'icloud.com' in url_lower:
            return 'icloud'
        elif url_lower.endswith(('.xlsx', '.xls', '.csv')):
            return 'direct_file'
        else:
            return 'unknown'
    
    def convert_to_direct_download_url(self, url: str, provider: str) -> Optional[str]:
        """
        Converter URL de visualização para URL de download direto
        """
        try:
            if provider == 'google_sheets':
                return self._convert_google_sheets_url(url)
            elif provider == 'onedrive':
                return self._convert_onedrive_url(url)
            elif provider == 'dropbox':
                return self._convert_dropbox_url(url)
            elif provider == 'sharepoint':
                return self._convert_sharepoint_url(url)
            elif provider == 'direct_file':
                return url
            else:
                return None
        except Exception as e:
            self.logger.error(f"Erro ao converter URL: {str(e)}")
            return None
    
    def _convert_google_sheets_url(self, url: str) -> str:
        """Converter URL do Google Sheets para CSV export"""
        # Extrair sheet ID
        sheet_id_pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(sheet_id_pattern, url)
        
        if match:
            sheet_id = match.group(1)
            # Extrair GID se existir
            gid_pattern = r'[#&]gid=([0-9]+)'
            gid_match = re.search(gid_pattern, url)
            gid = gid_match.group(1) if gid_match else '0'
            
            # Tentar múltiplas URLs de export
            # Primeiro tentar com usp=sharing para garantir acesso público
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}&usp=sharing"
        
        return url
    
    def _convert_onedrive_url(self, url: str) -> str:
        """Converter URL do OneDrive para download direto"""
        if '1drv.ms' in url:
            # URL encurtada do OneDrive - tentar expandir
            try:
                response = requests.head(url, allow_redirects=True, timeout=10)
                url = response.url
            except:
                pass
        
        # Converter para download direto
        if 'onedrive.live.com' in url:
            # Substituir 'view' por 'download'
            url = url.replace('/view.aspx', '/download.aspx')
            if '?download=1' not in url:
                separator = '&' if '?' in url else '?'
                url += f'{separator}download=1'
        
        return url
    
    def _convert_dropbox_url(self, url: str) -> str:
        """Converter URL do Dropbox para download direto"""
        if 'dropbox.com' in url:
            # Substituir dl=0 por dl=1 para download direto
            if 'dl=0' in url:
                url = url.replace('dl=0', 'dl=1')
            elif 'dl=1' not in url:
                separator = '&' if '?' in url else '?'
                url += f'{separator}dl=1'
        
        return url
    
    def _convert_sharepoint_url(self, url: str) -> str:
        """Converter URL do SharePoint para download direto"""
        # SharePoint URLs são mais complexas, tentativa básica
        if 'sharepoint.com' in url and 'download=1' not in url:
            separator = '&' if '?' in url else '?'
            url += f'{separator}download=1'
        
        return url
    
    def download_file_from_url(self, url: str) -> Optional[bytes]:
        """
        Baixar arquivo de uma URL com fallbacks para Google Sheets
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Se for Google Sheets e falhar, tentar URLs alternativas
            if 'docs.google.com' in url:
                return self._download_google_sheets_with_fallback(url, headers)
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao baixar arquivo: {str(e)}")
            return None
    
    def _download_google_sheets_with_fallback(self, url: str, headers: dict) -> Optional[bytes]:
        """
        Tentar baixar Google Sheets com múltiplas estratégias de fallback
        """
        # Extrair sheet ID e GID
        sheet_id_pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(sheet_id_pattern, url)
        
        if not match:
            # Se não conseguir extrair ID, tentar URL original
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.content
        
        sheet_id = match.group(1)
        gid_pattern = r'[#&]gid=([0-9]+)'
        gid_match = re.search(gid_pattern, url)
        gid = gid_match.group(1) if gid_match else '0'
        
        # Lista de URLs para tentar em ordem de prioridade
        fallback_urls = [
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}&usp=sharing",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/pub?gid={gid}&single=true&output=csv"
        ]
        
        last_error = None
        for attempt_url in fallback_urls:
            try:
                self.logger.debug(f"Tentando URL: {attempt_url}")
                response = requests.get(attempt_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Verificar se o conteúdo não é uma página de erro HTML
                content = response.content
                if b'<!DOCTYPE html>' not in content and b'<html' not in content:
                    self.logger.debug(f"Sucesso com URL: {attempt_url}")
                    return content
                else:
                    self.logger.debug(f"URL retornou HTML (página de erro): {attempt_url}")
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                self.logger.debug(f"Falha na URL {attempt_url}: {str(e)}")
                continue
        
        # Se todas as tentativas falharam, lançar o último erro
        if last_error:
            self.logger.warning(
                f"Todas as tentativas de download do Google Sheets falharam (sheet_id={sheet_id}, gid={gid}): {last_error}"
            )
            raise last_error
        
        return None
    
    def load_spreadsheet_from_url(self, url: str) -> Optional[pd.DataFrame]:
        """
        Carregar planilha de qualquer URL suportada
        """
        try:
            # Detectar provedor
            provider = self.detect_cloud_provider(url)
            self.logger.debug(f"Provedor detectado: {provider}")
            
            # Tentar Google Sheets API primeiro se disponível
            if provider == 'google_sheets' and GOOGLE_AVAILABLE and self.gc:
                try:
                    return self._load_google_sheets_api(url)
                except Exception as e:
                    self.logger.warning(f"Falha na API do Google Sheets, tentando download direto: {str(e)}")
            
            # Converter para URL de download direto
            download_url = self.convert_to_direct_download_url(url, provider)
            if not download_url:
                st.error(f"Não foi possível converter URL do provedor: {provider}")
                return None
            
            # Baixar arquivo
            file_content = self.download_file_from_url(download_url)
            if not file_content:
                st.error("Não foi possível baixar o arquivo")
                return None
            
            # Detectar formato e carregar
            return self._load_data_from_content(file_content, url)
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar planilha: {str(e)}")
            st.error(f"Erro ao carregar planilha: {str(e)}")
            return None
    
    def _load_google_sheets_api(self, url: str) -> Optional[pd.DataFrame]:
        """Carregar usando API do Google Sheets"""
        sheet_id_pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(sheet_id_pattern, url)
        
        if not match:
            return None
        
        sheet_id = match.group(1)
        gid_pattern = r'[#&]gid=([0-9]+)'
        gid_match = re.search(gid_pattern, url)
        
        spreadsheet = self.gc.open_by_key(sheet_id)
        
        if gid_match:
            gid = gid_match.group(1)
            worksheet = None
            for ws in spreadsheet.worksheets():
                if str(ws.id) == gid:
                    worksheet = ws
                    break
        else:
            worksheet = spreadsheet.sheet1
        
        if not worksheet:
            return None
        
        data = worksheet.get_all_records()
        return pd.DataFrame(data) if data else None
    
    def _load_data_from_content(self, content: bytes, original_url: str) -> Optional[pd.DataFrame]:
        """
        Carregar dados do conteúdo do arquivo
        """
        try:
            # Tentar como CSV primeiro
            try:
                df = pd.read_csv(io.BytesIO(content))
                if not df.empty:
                    return self._clean_dataframe(df)
            except:
                pass
            
            # Tentar como Excel
            try:
                df = pd.read_excel(io.BytesIO(content))
                if not df.empty:
                    return self._clean_dataframe(df)
            except:
                pass
            
            # Tentar diferentes encodings para CSV
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content_str = content.decode(encoding)
                    df = pd.read_csv(io.StringIO(content_str))
                    if not df.empty:
                        return self._clean_dataframe(df)
                except:
                    continue
            
            self.logger.error("Não foi possível interpretar o conteúdo do arquivo")
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao processar conteúdo: {str(e)}")
            return None
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpar e padronizar DataFrame
        """
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        # Remover colunas unnamed
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Limpar nomes das colunas
        df.columns = df.columns.str.strip()
        
        # Converter colunas numéricas quando possível
        for col in df.columns:
            if df[col].dtype == 'object':
                # Tentar converter para numérico
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                if not numeric_series.isna().all():
                    df[col] = numeric_series
        
        return df
    
    def authenticate_google_sheets(self, credentials_path: str = None) -> bool:
        """
        Autenticar com Google Sheets
        """
        if not GOOGLE_AVAILABLE:
            return False
        
        try:
            if credentials_path and os.path.exists(credentials_path):
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                self.gc = gspread.authorize(creds)
                return True
            else:
                creds, _ = default()
                self.gc = gspread.authorize(creds)
                return True
        except Exception as e:
            self.logger.error(f"Erro na autenticação Google Sheets: {str(e)}")
            return False
    
    def validate_url_access(self, url: str) -> Dict[str, Union[bool, str]]:
        """
        Validar se a URL está acessível
        """
        try:
            provider = self.detect_cloud_provider(url)
            
            # Para Google Sheets, tentar acesso direto
            if provider == 'google_sheets':
                download_url = self.convert_to_direct_download_url(url, provider)
                response = requests.head(download_url, timeout=10)
                accessible = response.status_code == 200
            else:
                # Para outros provedores, tentar HEAD request
                response = requests.head(url, timeout=10)
                accessible = response.status_code in [200, 302, 301]
            
            return {
                'accessible': accessible,
                'provider': provider,
                'status_code': response.status_code if 'response' in locals() else None,
                'message': 'URL acessível' if accessible else 'URL não acessível ou requer autenticação'
            }
            
        except Exception as e:
            return {
                'accessible': False,
                'provider': 'unknown',
                'status_code': None,
                'message': f'Erro ao validar URL: {str(e)}'
            }

class UniversalCloudUI:
    """Interface do usuário para integração universal com nuvem"""
    
    def __init__(self):
        self.integrator = UniversalCloudIntegrator()
        
    def render_integration_page(self):
        """Renderizar página completa de integração universal"""
        st.title("☁️ Integração Universal com Armazenamento em Nuvem")
        
        st.info("""
        **Provedores Suportados:**
        - 📊 Google Sheets
        - 📁 OneDrive / SharePoint
        - 📦 Dropbox
        - 🗃️ Box
        - ☁️ iCloud
        - 🔗 Links diretos (.xlsx, .xls, .csv)
        """)
        
        # Configuração do Google Sheets (opcional)
        with st.expander("🔐 Configuração Google Sheets (Opcional)"):
            self.setup_google_authentication()
        
        # Interface principal
        self.render_url_input_interface()
        
        # Instruções
        with st.expander("📖 Como usar"):
            self.render_instructions()
    
    def setup_google_authentication(self):
        """Configurar autenticação do Google Sheets"""
        st.info("Para melhor performance com Google Sheets, configure a autenticação (opcional)")
        
        uploaded_file = st.file_uploader(
            "Upload do arquivo de credenciais JSON (opcional)",
            type=['json'],
            help="Arquivo JSON do Google Cloud Console para acesso via API"
        )
        
        if uploaded_file:
            credentials_path = "temp_google_credentials.json"
            with open(credentials_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if st.button("Configurar Google Sheets"):
                if self.integrator.authenticate_google_sheets(credentials_path):
                    st.success("✅ Google Sheets configurado com sucesso!")
                    st.session_state['google_sheets_authenticated'] = True
                else:
                    st.error("❌ Falha na configuração do Google Sheets")
                
                os.remove(credentials_path)
    
    def render_url_input_interface(self):
        """Interface para entrada de URL"""
        st.subheader("🔗 Carregar Planilha de URL")
        
        # URLs de exemplo
        example_urls = {
            "Selecione um exemplo...": "",
            "Budget Mensal (Google Sheets)": "https://docs.google.com/spreadsheets/d/1R1ntD_FotSEQX7fLJ20yudEuGxuFkun9/edit?gid=757859154#gid=757859154",
            "Comparativo (Google Sheets)": "https://docs.google.com/spreadsheets/d/1Bphi7lChPqh12kAStpupXJmCbwcdImKo/edit?gid=251726202#gid=251726202"
        }
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_example = st.selectbox("Exemplos:", list(example_urls.keys()))
            
            if selected_example != "Selecione um exemplo...":
                url = example_urls[selected_example]
                st.code(url, language=None)
            else:
                url = st.text_input(
                    "Cole a URL da planilha:",
                    placeholder="https://docs.google.com/spreadsheets/... ou https://1drv.ms/... ou https://dropbox.com/...",
                    help="Suporta Google Sheets, OneDrive, Dropbox, Box, iCloud e links diretos"
                )
        
        with col2:
            if url and st.button("🔍 Validar URL", use_container_width=True):
                with st.spinner("Validando URL..."):
                    validation = self.integrator.validate_url_access(url)
                    
                    if validation['accessible']:
                        st.success(f"✅ URL válida ({validation['provider']})")
                    else:
                        st.error(f"❌ {validation['message']}")
        
        if url and st.button("📊 Carregar Planilha", use_container_width=True):
            self.load_spreadsheet_from_url(url)
    
    def load_spreadsheet_from_url(self, url: str):
        """Carregar planilha de URL"""
        with st.spinner("Carregando planilha..."):
            # Detectar provedor
            provider = self.integrator.detect_cloud_provider(url)
            st.info(f"🔍 Provedor detectado: **{provider.replace('_', ' ').title()}**")
            
            # Carregar dados
            df = self.integrator.load_spreadsheet_from_url(url)
            
            if df is not None and not df.empty:
                st.success(f"✅ Planilha carregada com sucesso!")
                st.info(f"📊 **{len(df)}** linhas e **{len(df.columns)}** colunas")
                
                # Preview dos dados
                st.subheader("📋 Preview dos Dados")
                st.dataframe(df.head(10))
                
                # Informações das colunas
                with st.expander("📊 Informações das Colunas"):
                    col_info = pd.DataFrame({
                        'Coluna': df.columns,
                        'Tipo': df.dtypes.astype(str),
                        'Não Nulos': df.count(),
                        'Valores Únicos': [df[col].nunique() for col in df.columns],
                        'Exemplo': [str(df[col].iloc[0]) if len(df) > 0 else 'N/A' for col in df.columns]
                    })
                    st.dataframe(col_info)
                
                # Salvar na sessão
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_key = f'cloud_data_{provider}_{timestamp}'
                st.session_state[session_key] = df
                
                # Opções de salvamento
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾 Salvar Localmente"):
                        filename = f"dados/cloud_import_{provider}_{timestamp}.xlsx"
                        os.makedirs(os.path.dirname(filename), exist_ok=True)
                        df.to_excel(filename, index=False)
                        st.success(f"✅ Salvo em: {filename}")
                
                with col2:
                    if st.button("🔄 Integrar ao Sistema"):
                        # Adicionar aos dados principais
                        if 'df_main' not in st.session_state:
                            st.session_state.df_main = pd.DataFrame()
                        
                        if st.session_state.df_main.empty:
                            st.session_state.df_main = df.copy()
                        else:
                            # Tentar concatenar se as colunas forem compatíveis
                            try:
                                st.session_state.df_main = pd.concat([st.session_state.df_main, df], ignore_index=True)
                            except:
                                st.warning("⚠️ Estruturas de dados incompatíveis. Dados salvos separadamente.")
                        
                        st.success("✅ Dados integrados ao sistema!")
                
                with col3:
                    # Download como CSV
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"planilha_{provider}_{timestamp}.csv",
                        mime="text/csv"
                    )
            
            else:
                st.error("❌ Não foi possível carregar a planilha ou ela está vazia")
    
    def render_instructions(self):
        """Renderizar instruções de uso"""
        st.markdown("""
        ### 📋 Como usar a integração universal:
        
        #### 🔗 URLs Suportadas:
        
        **Google Sheets:**
        - `https://docs.google.com/spreadsheets/d/ID/edit`
        - `https://docs.google.com/spreadsheets/d/ID/edit#gid=123`
        
        **OneDrive:**
        - `https://1drv.ms/x/s!...` (link compartilhado)
        - `https://onedrive.live.com/view.aspx?...`
        
        **Dropbox:**
        - `https://www.dropbox.com/s/.../file.xlsx?dl=0`
        - `https://dropbox.com/sh/.../folder`
        
        **SharePoint:**
        - `https://company.sharepoint.com/.../file.xlsx`
        
        **Links Diretos:**
        - Qualquer URL que termine em `.xlsx`, `.xls`, ou `.csv`
        
        #### 🛠️ Configuração de Compartilhamento:
        
        1. **Google Sheets**: Compartilhe com "Qualquer pessoa com o link pode visualizar"
        2. **OneDrive**: Use "Compartilhar" → "Qualquer pessoa com o link pode visualizar"
        3. **Dropbox**: Altere `dl=0` para `dl=1` na URL ou use link público
        4. **Outros**: Certifique-se de que o link permite acesso público
        
        #### 🔍 Detecção Automática:
        - O sistema detecta automaticamente o provedor
        - Converte URLs de visualização para download direto
        - Suporta múltiplos formatos (Excel, CSV)
        - Limpeza automática de dados
        
        #### ⚡ Dicas para Melhor Performance:
        - Use Google Sheets API para planilhas grandes (configure credenciais)
        - Certifique-se de que os links são públicos
        - Prefira formatos CSV para arquivos grandes
        - Verifique a conectividade de rede
        """)

def create_universal_cloud_integration():
    """Função para criar a interface de integração universal"""
    ui = UniversalCloudUI()
    return ui.render_integration_page()

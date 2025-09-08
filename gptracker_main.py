"""
GPTRACKER - Sistema Integrado de Análise Comercial e Logística
Aplicação principal que integra todos os módulos desenvolvidos
"""
import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

# Imports dos módulos desenvolvidos
from src.auth import auth_manager
from src.dashboard import dashboard
from src.budget_manager import BudgetManager
from src.predictive_analytics import PredictiveAnalytics
from src.advanced_llm import AdvancedLLMManager
from src.data_ingestion import DataIngestionManager
from src.security_manager import SecurityManager
from src.universal_cloud_integration import UniversalCloudUI

class GPTracker:
    def __init__(self):
        self.budget_manager = BudgetManager()
        self.predictive_analytics = PredictiveAnalytics()
        self.setup_page_config()
        self.initialize_session_state()
        
    def setup_page_config(self):
        """Configuração inicial da página"""
        st.set_page_config(
            page_title="GPTRACKER - Itracker AI Assistant",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS customizado
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e86ab 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #2e86ab;
        }
        .sidebar-section {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Inicializa estado da sessão"""
        if 'df_main' not in st.session_state:
            st.session_state.df_main = pd.DataFrame()
        if 'last_data_update' not in st.session_state:
            st.session_state.last_data_update = None
        if 'knowledge_base_updated' not in st.session_state:
            st.session_state.knowledge_base_updated = False
    
    def load_main_data(self):
        """Carrega dados principais"""
        try:
            # Verificar se existe arquivo consolidado
            consolidated_file = "dados/Dados_Consolidados.xlsx"
            if os.path.exists(consolidated_file):
                df = pd.read_excel(consolidated_file)
                
                # Processamento básico
                if not df.empty:
                    # Padronizar colunas
                    if 'ANO/MÊS' in df.columns:
                        df['ano_mes'] = pd.to_numeric(df['ANO/MÊS'], errors='coerce')
                        df['ano'] = df['ano_mes'] // 100
                        df['mes'] = df['ano_mes'] % 100
                    
                    # Unificar quantidade de containers
                    colunas_qtd = ['QTDE CONTAINER', 'QTDE CONTEINER', 'C20', 'C40']
                    df['qtd_container'] = 0
                    for col in colunas_qtd:
                        if col in df.columns:
                            df['qtd_container'] += pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
                    # Padronizar cliente
                    client_cols = ['CONSIGNATÁRIO', 'NOME EXPORTADOR', 'DESTINATÁRIO']
                    for col in client_cols:
                        if col in df.columns and 'cliente' not in df.columns:
                            df['cliente'] = df[col]
                            break
                    
                    # Mapear categoria para tipo_operacao
                    if 'Categoria' in df.columns:
                        categoria_map = {
                            'Importação': 'importacao',
                            'Exportação': 'exportacao', 
                            'Cabotagem': 'cabotagem'
                        }
                        df['tipo_operacao'] = df['Categoria'].map(categoria_map)
                
                st.session_state.df_main = df
                st.session_state.last_data_update = datetime.now()
                
                # Atualizar base de conhecimento se necessário
                if not st.session_state.knowledge_base_updated:
                    with st.spinner("Atualizando base de conhecimento..."):
                        advanced_llm.update_knowledge_base(df)
                        st.session_state.knowledge_base_updated = True
                
                return df
            else:
                st.error("Arquivo de dados consolidados não encontrado")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return pd.DataFrame()
    
    def render_sidebar(self):
        """Renderiza barra lateral com navegação"""
        with st.sidebar:
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.image("https://via.placeholder.com/200x80/2e86ab/white?text=GPTRACKER", width=200)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Informações do usuário
            if st.session_state.get('authenticated', False):
                username = st.session_state.get('username', 'Usuário')
                user_info = auth_manager.get_user_info(username)
                role = user_info.get('role', 'user') if user_info else 'user'
                
                st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
                st.write(f"👤 **{username}**")
                st.write(f"🏷️ {role.title()}")
                
                if st.button("🚪 Logout", use_container_width=True):
                    auth_manager.logout()
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Menu de navegação
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("📋 Menu")
            
            # Navegação principal
            pages = {
                "🏠 Dashboard": "dashboard",
                "💬 Chat GPT": "chat",
                "📊 Analytics": "analytics", 
                "🎯 Budget & Metas": "budget",
                "📁 Gestão de Dados": "data_management",
                "☁️ Nuvem Universal": "cloud_integration",
                "🔒 Segurança": "security"
            }
            
            selected_page = st.radio("Selecione uma opção:", list(pages.keys()))
            st.session_state.current_page = pages[selected_page]
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Status do sistema
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("📊 Status do Sistema")
            
            if not st.session_state.df_main.empty:
                st.success("✅ Dados carregados")
                st.write(f"📦 {len(st.session_state.df_main):,} registros")
                if st.session_state.last_data_update:
                    st.write(f"🕐 Atualizado: {st.session_state.last_data_update.strftime('%H:%M')}")
            else:
                st.warning("⚠️ Dados não carregados")
            
            if st.button("🔄 Recarregar Dados", use_container_width=True):
                st.session_state.df_main = pd.DataFrame()
                st.session_state.knowledge_base_updated = False
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_dashboard_page(self):
        """Renderiza página do dashboard"""
        st.markdown('<div class="main-header"><h1>📊 Dashboard Executivo</h1></div>', unsafe_allow_html=True)
        
        if st.session_state.df_main.empty:
            st.warning("Carregue os dados para visualizar o dashboard")
            return
        
        dashboard.render_full_dashboard(st.session_state.df_main)
    
    def render_chat_page(self):
        """Renderiza página do chat"""
        st.markdown('<div class="main-header"><h1>💬 GPTRACKER Chat</h1></div>', unsafe_allow_html=True)
        
        if st.session_state.df_main.empty:
            st.warning("Carregue os dados para usar o chat")
            return
        
        # Histórico de conversas
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Exibir histórico
        for i, (question, answer) in enumerate(st.session_state.chat_history):
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                st.write(answer)
        
        # Input para nova pergunta
        user_question = st.chat_input("Faça sua pergunta sobre os dados...")
        
        if user_question:
            with st.chat_message("user"):
                st.write(user_question)
            
            with st.chat_message("assistant"):
                with st.spinner("Analisando..."):
                    # Usar LLM avançado com RAG
                    response = advanced_llm.generate_enhanced_response(
                        user_question, 
                        st.session_state.df_main
                    )
                    st.write(response)
                    
                    # Adicionar ao histórico
                    st.session_state.chat_history.append((user_question, response))
                    
                    # Limitar histórico a 10 conversas
                    if len(st.session_state.chat_history) > 10:
                        st.session_state.chat_history = st.session_state.chat_history[-10:]
        
        # Insights proativos
        if st.session_state.df_main is not None and not st.session_state.df_main.empty:
            with st.expander("💡 Insights Proativos", expanded=False):
                insights = advanced_llm.generate_proactive_insights(st.session_state.df_main)
                for insight in insights:
                    st.write(insight)
    
    def render_analytics_page(self):
        """Renderiza página de análises"""
        st.markdown('<div class="main-header"><h1>📈 Análises Avançadas</h1></div>', unsafe_allow_html=True)
        
        if st.session_state.df_main.empty:
            st.warning("Carregue os dados para visualizar análises")
            return
        
        tab1, tab2, tab3 = st.tabs(["🔮 Previsões", "🎯 Oportunidades", "📊 Sazonalidade"])
        
        with tab1:
            st.subheader("Previsão de Demanda")
            
            months_ahead = st.slider("Meses para prever:", 1, 12, 3)
            
            if st.button("Gerar Previsão"):
                with st.spinner("Calculando previsões..."):
                    forecast = predictive_analytics.predict_demand(st.session_state.df_main, months_ahead)
                    
                    if "error" not in forecast:
                        st.success("Previsão gerada com sucesso!")
                        
                        # Exibir previsões
                        for pred in forecast["previsoes"]:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Mês", pred["mes"])
                            with col2:
                                st.metric("Containers Previstos", f"{pred['containers_previstos']:,}")
                            with col3:
                                st.metric("Confiança", pred["confianca"])
                        
                        # Métricas do modelo
                        st.subheader("Qualidade da Previsão")
                        metrics = forecast["metricas_modelo"]
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Precisão", metrics["precisao"])
                        with col2:
                            st.metric("R²", f"{metrics['r2']:.3f}")
                    else:
                        st.error(forecast["error"])
        
        with tab2:
            st.subheader("Oportunidades de Crescimento")
            
            opportunities = predictive_analytics.identify_growth_opportunities(st.session_state.df_main)
            
            if opportunities:
                for i, opp in enumerate(opportunities[:10]):
                    with st.expander(f"Oportunidade {i+1}: {opp['tipo'].replace('_', ' ').title()}"):
                        st.write(f"**Potencial:** {opp['potencial']}")
                        st.write(f"**Descrição:** {opp['descricao']}")
                        st.write(f"**Ação Sugerida:** {opp['acao_sugerida']}")
                        
                        if 'cliente' in opp:
                            st.write(f"**Cliente:** {opp['cliente']}")
            else:
                st.info("Nenhuma oportunidade identificada no momento")
        
        with tab3:
            st.subheader("Análise de Sazonalidade")
            
            seasonality = predictive_analytics.analyze_seasonality(st.session_state.df_main)
            
            if "error" not in seasonality:
                # Pico e vale sazonal
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Pico Sazonal", 
                        f"Mês {seasonality['pico_sazonal']['mes']}", 
                        f"{seasonality['pico_sazonal']['valor']:,} containers"
                    )
                with col2:
                    st.metric(
                        "Vale Sazonal", 
                        f"Mês {seasonality['vale_sazonal']['mes']}", 
                        f"{seasonality['vale_sazonal']['valor']:,} containers"
                    )
                
                st.metric("Amplitude Sazonal", f"{seasonality['amplitude_sazonal']:.1f}%")
                
                # Detalhes mensais
                st.subheader("Variação Mensal")
                monthly_data = seasonality["sazonalidade_mensal"]
                
                for mes, data in monthly_data.items():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Mês {mes}**")
                    with col2:
                        st.write(f"{data['media_containers']:,} containers")
                    with col3:
                        variation = data['variacao_percentual']
                        color = "green" if variation > 0 else "red" if variation < 0 else "gray"
                        st.markdown(f"<span style='color: {color}'>{variation:+.1f}%</span>", unsafe_allow_html=True)
            else:
                st.error(seasonality["error"])
    
    def render_budget_page(self):
        """Renderiza página de budget e metas"""
        if not auth_manager.has_permission(st.session_state.get('username', ''), 'budget'):
            st.error("Você não tem permissão para acessar dados de budget")
            return
        
        st.markdown('<div class="main-header"><h1>🎯 Budget & Metas</h1></div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📊 Performance", "🎯 Definir Metas", "💡 Insights"])
        
        with tab1:
            if not st.session_state.df_main.empty:
                dashboard.render_budget_performance(st.session_state.df_main)
        
        with tab2:
            st.subheader("Definir Metas")
            
            meta_type = st.selectbox("Tipo de Meta:", ["Anual", "Mensal", "Por Cliente"])
            
            if meta_type == "Anual":
                col1, col2 = st.columns(2)
                with col1:
                    ano = st.number_input("Ano:", min_value=2024, max_value=2030, value=2025)
                    receita_total = st.number_input("Meta de Receita (R$):", min_value=0.0, value=1000000.0)
                with col2:
                    containers_total = st.number_input("Meta de Containers:", min_value=0, value=10000)
                    novos_clientes = st.number_input("Novos Clientes:", min_value=0, value=50)
                
                if st.button("Salvar Meta Anual"):
                    self.budget_manager.set_annual_goals(ano, receita_total, containers_total, novos_clientes)
                    st.success("Meta anual salva com sucesso!")
            
            elif meta_type == "Mensal":
                col1, col2, col3 = st.columns(3)
                with col1:
                    ano = st.number_input("Ano:", min_value=2024, max_value=2030, value=2025)
                with col2:
                    mes = st.number_input("Mês:", min_value=1, max_value=12, value=1)
                with col3:
                    receita = st.number_input("Meta de Receita (R$):", min_value=0.0, value=100000.0)
                
                containers = st.number_input("Meta de Containers:", min_value=0, value=1000)
                
                if st.button("Salvar Meta Mensal"):
                    self.budget_manager.set_monthly_goals(ano, mes, receita, containers)
                    st.success("Meta mensal salva com sucesso!")
        
        with tab3:
            if not st.session_state.df_main.empty:
                insights = self.budget_manager.generate_budget_insights(st.session_state.df_main)
                for insight in insights:
                    st.write(insight)
    
    def render_data_management_page(self):
        """Renderiza página de gestão de dados"""
        if not auth_manager.has_permission(st.session_state.get('username', ''), 'write'):
            st.error("Você não tem permissão para gerenciar dados")
            return
        
        st.markdown('<div class="main-header"><h1>📁 Gestão de Dados</h1></div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📤 Upload", "📊 Status", "🔍 Validação"])
        
        with tab1:
            st.subheader("Upload de Novos Dados")
            
            uploaded_file = st.file_uploader(
                "Selecione um arquivo:",
                type=['xlsx', 'xls', 'csv'],
                help="Formatos suportados: Excel (.xlsx, .xls) e CSV"
            )
            
            if uploaded_file:
                schema_type = st.selectbox(
                    "Tipo de dados:",
                    ["Auto-detectar", "Logístico", "Comercial", "Budget", "Oportunidades"]
                )
                
                if st.button("Processar Arquivo"):
                    # Salvar arquivo temporariamente
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Processar
                    schema_name = None if schema_type == "Auto-detectar" else schema_type.lower()
                    result = data_ingestion.process_file(temp_path, schema_name)
                    
                    # Limpar arquivo temporário
                    os.remove(temp_path)
                    
                    if result["success"]:
                        st.success("Arquivo processado com sucesso!")
                        st.json(result)
                    else:
                        st.error(f"Erro no processamento: {result['error']}")
        
        with tab2:
            st.subheader("Status do Sistema")
            status = data_ingestion.get_processing_status()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Arquivos Processados", status["processed_files"])
            with col2:
                st.metric("Arquivos Arquivados", status["archived_files"])
            with col3:
                st.metric("Formatos Suportados", len(status["supported_formats"]))
        
        with tab3:
            st.subheader("Validação de Dados")
            
            if not st.session_state.df_main.empty:
                if st.button("Executar Validação"):
                    with st.spinner("Validando dados..."):
                        validation = security_manager.validate_data_integrity(st.session_state.df_main)
                        quality = security_manager.check_data_quality(st.session_state.df_main)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Integridade dos Dados")
                            if validation["valid"]:
                                st.success("✅ Dados íntegros")
                            else:
                                st.error("❌ Problemas encontrados")
                                for issue in validation["issues"]:
                                    st.write(f"• {issue}")
                        
                        with col2:
                            st.subheader("Qualidade dos Dados")
                            st.metric("Score de Qualidade", f"{quality['score']}/100")
                            
                            if quality["issues"]:
                                st.write("**Problemas identificados:**")
                                for issue in quality["issues"]:
                                    st.write(f"• {issue}")
    
    def render_security_page(self):
        """Renderiza página de segurança"""
        if not auth_manager.has_permission(st.session_state.get('username', ''), 'admin'):
            st.error("Você não tem permissão para acessar configurações de segurança")
            return
        
        st.markdown('<div class="main-header"><h1>🔒 Segurança & Auditoria</h1></div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📋 Relatório de Segurança", "📊 Logs de Acesso"])
        
        with tab1:
            if st.button("Gerar Relatório de Segurança"):
                with st.spinner("Gerando relatório..."):
                    username = st.session_state.get('username', 'admin')
                    report = security_manager.generate_security_report(st.session_state.df_main, username)
                    
                    st.json(report)
        
        with tab2:
            st.subheader("Logs de Acesso Recentes")
            username_filter = st.text_input("Filtrar por usuário (opcional):")
            
            if st.button("Carregar Logs"):
                logs = security_manager.get_access_logs(username_filter if username_filter else None)
                
                if logs:
                    for log in logs[-20:]:  # Últimos 20 logs
                        st.text(f"{log['timestamp']} - {log['message']}")
                else:
                    st.info("Nenhum log encontrado")
    
    def render_cloud_integration_page(self):
        """Renderiza página de integração universal com nuvem"""
        cloud_ui = UniversalCloudUI()
        cloud_ui.render_integration_page()
    
    def run(self):
        """Executa aplicação principal"""
        # Verificar autenticação
        if not auth_manager.require_auth():
            return
        
        # Inicializar usuários padrão se necessário
        auth_manager.init_default_users()
        
        # Carregar dados principais
        if st.session_state.df_main.empty:
            with st.spinner("Carregando dados..."):
                self.load_main_data()
        
        # Renderizar sidebar
        self.render_sidebar()
        
        # Renderizar página selecionada
        current_page = st.session_state.get('current_page', 'dashboard')
        
        if current_page == 'dashboard':
            self.render_dashboard_page()
        elif current_page == 'chat':
            self.render_chat_page()
        elif current_page == 'analytics':
            self.render_analytics_page()
        elif current_page == 'budget':
            self.render_budget_page()
        elif current_page == 'data_management':
            self.render_data_management_page()
        elif current_page == 'cloud_integration':
            self.render_cloud_integration_page()
        elif current_page == 'security':
            self.render_security_page()

if __name__ == "__main__":
    app = GPTracker()
    app.run()

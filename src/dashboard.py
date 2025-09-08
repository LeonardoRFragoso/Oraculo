"""
Dashboard executivo para GPTRACKER
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from .budget_manager import BudgetManager
from .auth import auth_manager

class ExecutiveDashboard:
    def __init__(self):
        self.budget_manager = BudgetManager()
        
    def render_kpi_cards(self, df: pd.DataFrame):
        """Renderiza cards de KPIs principais"""
        if df.empty:
            st.warning("Nenhum dado disponível para exibir KPIs")
            return
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Filtrar dados do mês atual
        df_current = df[
            (df['ano'] == current_year) & 
            (df['mes'] == current_month)
        ] if 'ano' in df.columns and 'mes' in df.columns else df
        
        # Calcular KPIs
        total_containers = df_current['qtd_container'].sum()
        total_operacoes = len(df_current)
        clientes_unicos = df_current['cliente'].nunique() if 'cliente' in df_current.columns else 0
        
        # Comparar com mês anterior
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1
        
        df_prev = df[
            (df['ano'] == prev_year) & 
            (df['mes'] == prev_month)
        ] if 'ano' in df.columns and 'mes' in df.columns else pd.DataFrame()
        
        prev_containers = df_prev['qtd_container'].sum() if not df_prev.empty else 0
        
        # Calcular variação
        if prev_containers > 0:
            variacao = ((total_containers - prev_containers) / prev_containers) * 100
        else:
            variacao = 0
        
        # Renderizar cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Containers (Mês Atual)",
                f"{total_containers:,.0f}",
                f"{variacao:+.1f}%" if variacao != 0 else None
            )
        
        with col2:
            st.metric(
                "Operações",
                f"{total_operacoes:,.0f}",
                None
            )
        
        with col3:
            st.metric(
                "Clientes Únicos",
                f"{clientes_unicos:,.0f}",
                None
            )
        
        with col4:
            media_containers = total_containers / total_operacoes if total_operacoes > 0 else 0
            st.metric(
                "Média Containers/Op",
                f"{media_containers:.1f}",
                None
            )
    
    def render_budget_performance(self, df: pd.DataFrame):
        """Renderiza performance vs budget"""
        if not auth_manager.has_permission(st.session_state.get('username', ''), 'budget'):
            st.warning("Você não tem permissão para visualizar dados de budget")
            return
        
        st.subheader("📊 Performance vs Budget")
        
        comparison = self.budget_manager.get_budget_vs_actual(df)
        
        if not comparison.get('anual') and not comparison.get('mensal'):
            st.info("Configure metas para visualizar a performance")
            return
        
        col1, col2 = st.columns(2)
        
        # Performance Anual
        with col1:
            if 'anual' in comparison and 'containers' in comparison['anual']:
                data = comparison['anual']['containers']
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = data['percentual'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Meta Anual (%)"},
                    delta = {'reference': 100},
                    gauge = {
                        'axis': {'range': [None, 150]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "orange"},
                            {'range': [100, 150], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                st.metric(
                    "Containers Anuais",
                    f"{data['realizado']:,.0f}",
                    f"Meta: {data['meta']:,.0f}"
                )
        
        # Performance Mensal
        with col2:
            if 'mensal' in comparison and 'containers' in comparison['mensal']:
                data = comparison['mensal']['containers']
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = data['percentual'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Meta Mensal (%)"},
                    delta = {'reference': 100},
                    gauge = {
                        'axis': {'range': [None, 150]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "orange"},
                            {'range': [100, 150], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                st.metric(
                    "Containers Mensais",
                    f"{data['realizado']:,.0f}",
                    f"Meta: {data['meta']:,.0f}"
                )
    
    def render_trend_analysis(self, df: pd.DataFrame):
        """Renderiza análise de tendências"""
        st.subheader("📈 Análise de Tendências")
        
        if df.empty or 'ano_mes' not in df.columns:
            st.warning("Dados insuficientes para análise de tendências")
            return
        
        # Preparar dados mensais
        monthly_data = df.groupby('ano_mes').agg({
            'qtd_container': 'sum',
            'cliente': 'nunique'
        }).reset_index()
        
        monthly_data['data'] = pd.to_datetime(monthly_data['ano_mes'].astype(str), format='%Y%m')
        monthly_data = monthly_data.sort_values('data')
        
        # Gráfico de tendência
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Volume de Containers', 'Número de Clientes'),
            vertical_spacing=0.1
        )
        
        # Containers
        fig.add_trace(
            go.Scatter(
                x=monthly_data['data'],
                y=monthly_data['qtd_container'],
                mode='lines+markers',
                name='Containers',
                line=dict(color='blue', width=3)
            ),
            row=1, col=1
        )
        
        # Clientes
        fig.add_trace(
            go.Scatter(
                x=monthly_data['data'],
                y=monthly_data['cliente'],
                mode='lines+markers',
                name='Clientes',
                line=dict(color='green', width=3)
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=500,
            title_text="Tendências Mensais",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights de tendência
        if len(monthly_data) >= 3:
            recent_trend = monthly_data.tail(3)
            if recent_trend['qtd_container'].iloc[-1] > recent_trend['qtd_container'].iloc[0]:
                st.success("📈 Tendência de crescimento nos últimos 3 meses")
            else:
                st.warning("📉 Tendência de queda nos últimos 3 meses")
    
    def render_operational_analysis(self, df: pd.DataFrame):
        """Renderiza análise operacional"""
        st.subheader("🚢 Análise Operacional")
        
        if df.empty:
            st.warning("Nenhum dado disponível para análise operacional")
            return
        
        col1, col2 = st.columns(2)
        
        # Análise por tipo de operação
        with col1:
            if 'tipo_operacao' in df.columns:
                op_data = df.groupby('tipo_operacao')['qtd_container'].sum().reset_index()
                
                fig = px.pie(
                    op_data,
                    values='qtd_container',
                    names='tipo_operacao',
                    title='Distribuição por Tipo de Operação'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Top 10 clientes
        with col2:
            if 'cliente' in df.columns:
                top_clients = df.groupby('cliente')['qtd_container'].sum().nlargest(10).reset_index()
                
                fig = px.bar(
                    top_clients,
                    x='qtd_container',
                    y='cliente',
                    orientation='h',
                    title='Top 10 Clientes por Volume'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    def render_opportunities(self, df: pd.DataFrame):
        """Renderiza oportunidades comerciais"""
        if not auth_manager.has_permission(st.session_state.get('username', ''), 'analytics'):
            return
        
        st.subheader("💡 Oportunidades Comerciais")
        
        opportunities = self.budget_manager.get_opportunities(df)
        
        if not opportunities:
            st.info("Nenhuma oportunidade identificada no momento")
            return
        
        for i, opp in enumerate(opportunities):
            with st.expander(f"Oportunidade {i+1}: {opp['tipo'].title()}", expanded=i<3):
                st.write(f"**Tipo:** {opp['tipo']}")
                st.write(f"**Descrição:** {opp['descricao']}")
                st.write(f"**Potencial:** {opp['potencial']}")
                
                if opp['tipo'] == 'upsell' and 'cliente' in opp:
                    st.write(f"**Cliente:** {opp['cliente']}")
    
    def render_budget_insights(self, df: pd.DataFrame):
        """Renderiza insights de budget"""
        if not auth_manager.has_permission(st.session_state.get('username', ''), 'budget'):
            return
        
        insights = self.budget_manager.generate_budget_insights(df)
        
        if insights:
            st.subheader("🎯 Insights de Performance")
            for insight in insights:
                st.write(insight)
    
    def render_full_dashboard(self, df: pd.DataFrame):
        """Renderiza dashboard completo"""
        st.title("📊 Dashboard Executivo GPTRACKER")
        
        # Verificar autenticação
        if not auth_manager.require_auth():
            return
        
        # Header com informações do usuário
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Bem-vindo, **{st.session_state.get('username', 'Usuário')}**")
        with col2:
            if st.button("🚪 Logout"):
                auth_manager.logout()
        
        if df.empty:
            st.error("Nenhum dado disponível para exibir no dashboard")
            return
        
        # KPIs principais
        self.render_kpi_cards(df)
        
        st.divider()
        
        # Performance vs Budget
        self.render_budget_performance(df)
        
        st.divider()
        
        # Análise de tendências
        self.render_trend_analysis(df)
        
        st.divider()
        
        # Análise operacional
        self.render_operational_analysis(df)
        
        st.divider()
        
        # Insights e oportunidades
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_budget_insights(df)
        
        with col2:
            self.render_opportunities(df)

# Instância global do dashboard
dashboard = ExecutiveDashboard()

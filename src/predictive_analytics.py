"""
Módulo de análises preditivas e insights comerciais para GPTRACKER
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

class PredictiveAnalytics:
    def __init__(self):
        self.scaler = StandardScaler()
        self.models = {}
        
    def prepare_time_series_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara dados para análise temporal"""
        if df.empty or 'ano_mes' not in df.columns:
            return pd.DataFrame()
        
        # Agregar dados por mês
        monthly_data = df.groupby('ano_mes').agg({
            'qtd_container': 'sum',
            'cliente': 'nunique'
        }).reset_index()
        
        monthly_data['data'] = pd.to_datetime(monthly_data['ano_mes'].astype(str), format='%Y%m')
        monthly_data = monthly_data.sort_values('data').reset_index(drop=True)
        
        # Criar features temporais
        monthly_data['mes'] = monthly_data['data'].dt.month
        monthly_data['trimestre'] = monthly_data['data'].dt.quarter
        monthly_data['ano'] = monthly_data['data'].dt.year
        monthly_data['mes_sequencial'] = range(len(monthly_data))
        
        # Médias móveis
        monthly_data['ma_3'] = monthly_data['qtd_container'].rolling(window=3).mean()
        monthly_data['ma_6'] = monthly_data['qtd_container'].rolling(window=6).mean()
        
        # Tendência
        if len(monthly_data) > 1:
            monthly_data['tendencia'] = monthly_data['qtd_container'].diff()
        
        return monthly_data
    
    def predict_demand(self, df: pd.DataFrame, months_ahead: int = 3) -> Dict:
        """Prediz demanda futura baseada em dados históricos"""
        time_series_data = self.prepare_time_series_data(df)
        
        if len(time_series_data) < 6:
            return {"error": "Dados insuficientes para previsão (mínimo 6 meses)"}
        
        # Preparar features para modelo
        features = ['mes_sequencial', 'mes', 'trimestre']
        X = time_series_data[features].dropna()
        y = time_series_data['qtd_container'].iloc[:len(X)]
        
        if len(X) < 3:
            return {"error": "Dados insuficientes após limpeza"}
        
        # Treinar modelo
        model = LinearRegression()
        model.fit(X, y)
        
        # Fazer previsões
        last_month = time_series_data['mes_sequencial'].max()
        last_date = time_series_data['data'].max()
        
        predictions = []
        for i in range(1, months_ahead + 1):
            future_date = last_date + timedelta(days=30 * i)
            future_features = [
                last_month + i,
                future_date.month,
                future_date.quarter
            ]
            
            prediction = model.predict([future_features])[0]
            predictions.append({
                'mes': future_date.strftime('%Y-%m'),
                'containers_previstos': max(0, int(prediction)),
                'confianca': self._calculate_confidence(model, X, y)
            })
        
        # Calcular métricas do modelo
        y_pred = model.predict(X)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        return {
            'previsoes': predictions,
            'metricas_modelo': {
                'mae': mae,
                'r2': r2,
                'precisao': 'Alta' if r2 > 0.7 else 'Média' if r2 > 0.4 else 'Baixa'
            },
            'dados_historicos': len(time_series_data)
        }
    
    def _calculate_confidence(self, model, X, y) -> str:
        """Calcula nível de confiança da previsão"""
        score = model.score(X, y)
        if score > 0.8:
            return 'Alta'
        elif score > 0.6:
            return 'Média'
        else:
            return 'Baixa'
    
    def analyze_seasonality(self, df: pd.DataFrame) -> Dict:
        """Analisa padrões sazonais nos dados"""
        time_series_data = self.prepare_time_series_data(df)
        
        if len(time_series_data) < 12:
            return {"error": "Dados insuficientes para análise sazonal (mínimo 12 meses)"}
        
        # Análise por mês
        monthly_avg = time_series_data.groupby('mes')['qtd_container'].mean()
        overall_avg = time_series_data['qtd_container'].mean()
        
        seasonality = {}
        for mes, avg in monthly_avg.items():
            variation = ((avg - overall_avg) / overall_avg) * 100
            seasonality[mes] = {
                'media_containers': int(avg),
                'variacao_percentual': round(variation, 1),
                'classificacao': 'Alto' if variation > 10 else 'Baixo' if variation < -10 else 'Normal'
            }
        
        # Identificar picos e vales
        pico_mes = monthly_avg.idxmax()
        vale_mes = monthly_avg.idxmin()
        
        return {
            'sazonalidade_mensal': seasonality,
            'pico_sazonal': {
                'mes': pico_mes,
                'valor': int(monthly_avg[pico_mes])
            },
            'vale_sazonal': {
                'mes': vale_mes,
                'valor': int(monthly_avg[vale_mes])
            },
            'amplitude_sazonal': round(((monthly_avg.max() - monthly_avg.min()) / overall_avg) * 100, 1)
        }
    
    def identify_growth_opportunities(self, df: pd.DataFrame) -> List[Dict]:
        """Identifica oportunidades de crescimento"""
        opportunities = []
        
        if df.empty:
            return opportunities
        
        # Análise por cliente
        if 'cliente' in df.columns:
            client_analysis = df.groupby('cliente').agg({
                'qtd_container': ['sum', 'count', 'mean'],
                'ano_mes': ['min', 'max']
            }).reset_index()
            
            client_analysis.columns = ['cliente', 'total_containers', 'num_operacoes', 'media_containers', 'primeiro_mes', 'ultimo_mes']
            
            # Clientes com potencial de upsell
            median_containers = client_analysis['total_containers'].median()
            high_frequency = client_analysis[client_analysis['num_operacoes'] >= 5]
            
            for _, client in high_frequency.iterrows():
                if client['total_containers'] < median_containers:
                    opportunities.append({
                        'tipo': 'upsell_cliente',
                        'cliente': client['cliente'],
                        'potencial': 'Alto',
                        'descricao': f"Cliente frequente ({client['num_operacoes']} ops) com volume baixo",
                        'acao_sugerida': 'Oferecer pacotes de maior volume'
                    })
        
        # Análise temporal - identificar meses com baixa performance
        time_series = self.prepare_time_series_data(df)
        if not time_series.empty:
            avg_containers = time_series['qtd_container'].mean()
            low_months = time_series[time_series['qtd_container'] < avg_containers * 0.7]
            
            for _, month in low_months.iterrows():
                opportunities.append({
                    'tipo': 'sazonalidade',
                    'periodo': month['data'].strftime('%Y-%m'),
                    'potencial': 'Médio',
                    'descricao': f"Mês com volume {month['qtd_container']:.0f} (70% abaixo da média)",
                    'acao_sugerida': 'Campanhas promocionais específicas'
                })
        
        # Análise por tipo de operação
        if 'tipo_operacao' in df.columns:
            op_analysis = df.groupby('tipo_operacao')['qtd_container'].sum()
            total_containers = op_analysis.sum()
            
            for operacao, containers in op_analysis.items():
                share = (containers / total_containers) * 100
                if share < 20:  # Menos de 20% do total
                    opportunities.append({
                        'tipo': 'diversificacao_operacao',
                        'operacao': operacao,
                        'potencial': 'Alto',
                        'descricao': f"Operação {operacao} representa apenas {share:.1f}% do volume",
                        'acao_sugerida': f'Expandir operações de {operacao}'
                    })
        
        return opportunities[:15]  # Limitar a 15 oportunidades
    
    def calculate_client_lifetime_value(self, df: pd.DataFrame) -> Dict:
        """Calcula valor do tempo de vida do cliente"""
        if df.empty or 'cliente' not in df.columns:
            return {}
        
        client_metrics = df.groupby('cliente').agg({
            'qtd_container': ['sum', 'mean'],
            'ano_mes': ['count', 'min', 'max']
        }).reset_index()
        
        client_metrics.columns = ['cliente', 'total_containers', 'avg_containers', 'num_meses', 'primeiro_mes', 'ultimo_mes']
        
        # Calcular duração do relacionamento em meses
        client_metrics['duracao_meses'] = (
            pd.to_datetime(client_metrics['ultimo_mes'].astype(str), format='%Y%m') -
            pd.to_datetime(client_metrics['primeiro_mes'].astype(str), format='%Y%m')
        ).dt.days / 30
        
        client_metrics['duracao_meses'] = client_metrics['duracao_meses'].fillna(1)
        
        # Calcular CLV simplificado (containers por mês * duração)
        client_metrics['clv_score'] = client_metrics['avg_containers'] * client_metrics['duracao_meses']
        
        # Classificar clientes
        top_clients = client_metrics.nlargest(10, 'clv_score')
        
        return {
            'top_clientes_clv': [
                {
                    'cliente': row['cliente'],
                    'clv_score': round(row['clv_score'], 2),
                    'total_containers': int(row['total_containers']),
                    'duracao_meses': round(row['duracao_meses'], 1),
                    'avg_mensal': round(row['avg_containers'], 1)
                }
                for _, row in top_clients.iterrows()
            ],
            'metricas_gerais': {
                'clv_medio': round(client_metrics['clv_score'].mean(), 2),
                'duracao_media': round(client_metrics['duracao_meses'].mean(), 1),
                'containers_medio_mensal': round(client_metrics['avg_containers'].mean(), 1)
            }
        }
    
    def generate_commercial_insights(self, df: pd.DataFrame) -> List[str]:
        """Gera insights comerciais baseados em análises preditivas"""
        insights = []
        
        # Previsão de demanda
        demand_forecast = self.predict_demand(df)
        if 'previsoes' in demand_forecast:
            next_month = demand_forecast['previsoes'][0]
            insights.append(
                f"📈 Previsão próximo mês: {next_month['containers_previstos']:,} containers "
                f"(confiança: {next_month['confianca']})"
            )
        
        # Análise sazonal
        seasonality = self.analyze_seasonality(df)
        if 'pico_sazonal' in seasonality:
            insights.append(
                f"🌟 Pico sazonal no mês {seasonality['pico_sazonal']['mes']} "
                f"({seasonality['pico_sazonal']['valor']:,} containers)"
            )
        
        # Oportunidades
        opportunities = self.identify_growth_opportunities(df)
        upsell_ops = [op for op in opportunities if op['tipo'] == 'upsell_cliente']
        if upsell_ops:
            insights.append(f"💡 {len(upsell_ops)} oportunidades de upsell identificadas")
        
        # CLV
        clv_data = self.calculate_client_lifetime_value(df)
        if 'metricas_gerais' in clv_data:
            insights.append(
                f"👥 Duração média do cliente: {clv_data['metricas_gerais']['duracao_media']:.1f} meses"
            )
        
        return insights

# Instância global
predictive_analytics = PredictiveAnalytics()

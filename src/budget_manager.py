"""
Módulo de gestão de budget e metas comerciais para GPTRACKER
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os

class BudgetManager:
    def __init__(self, budget_file="budget_data.json"):
        self.budget_file = budget_file
        self.current_year = datetime.now().year
        
    def load_budget_data(self) -> Dict:
        """Carrega dados de budget do arquivo"""
        if os.path.exists(self.budget_file):
            with open(self.budget_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._create_default_budget()
    
    def save_budget_data(self, data: Dict):
        """Salva dados de budget no arquivo"""
        with open(self.budget_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _create_default_budget(self) -> Dict:
        """Cria estrutura padrão de budget"""
        return {
            "metas_anuais": {
                str(self.current_year): {
                    "receita_total": 0,
                    "containers_total": 0,
                    "novos_clientes": 0,
                    "margem_lucro": 0.15
                }
            },
            "metas_mensais": {},
            "metas_por_cliente": {},
            "metas_por_operacao": {
                "importacao": {"containers": 0, "receita": 0},
                "exportacao": {"containers": 0, "receita": 0},
                "cabotagem": {"containers": 0, "receita": 0}
            },
            "realizacoes": {
                "mensal": {},
                "anual": {},
                "por_cliente": {},
                "por_operacao": {}
            }
        }
    
    def set_annual_goals(self, year: int, receita_total: float, containers_total: int, 
                        novos_clientes: int, margem_lucro: float = 0.15):
        """Define metas anuais"""
        data = self.load_budget_data()
        
        data["metas_anuais"][str(year)] = {
            "receita_total": receita_total,
            "containers_total": containers_total,
            "novos_clientes": novos_clientes,
            "margem_lucro": margem_lucro,
            "updated_at": datetime.now().isoformat()
        }
        
        self.save_budget_data(data)
    
    def set_monthly_goals(self, year: int, month: int, receita: float, containers: int):
        """Define metas mensais"""
        data = self.load_budget_data()
        
        month_key = f"{year}-{month:02d}"
        if "metas_mensais" not in data:
            data["metas_mensais"] = {}
        
        data["metas_mensais"][month_key] = {
            "receita": receita,
            "containers": containers,
            "updated_at": datetime.now().isoformat()
        }
        
        self.save_budget_data(data)
    
    def set_client_goals(self, cliente: str, receita_anual: float, containers_anuais: int):
        """Define metas por cliente"""
        data = self.load_budget_data()
        
        if "metas_por_cliente" not in data:
            data["metas_por_cliente"] = {}
        
        data["metas_por_cliente"][cliente] = {
            "receita_anual": receita_anual,
            "containers_anuais": containers_anuais,
            "updated_at": datetime.now().isoformat()
        }
        
        self.save_budget_data(data)
    
    def update_realization(self, periodo: str, tipo: str, valor: Dict):
        """Atualiza realizações"""
        data = self.load_budget_data()
        
        if "realizacoes" not in data:
            data["realizacoes"] = {"mensal": {}, "anual": {}, "por_cliente": {}, "por_operacao": {}}
        
        if tipo not in data["realizacoes"]:
            data["realizacoes"][tipo] = {}
        
        data["realizacoes"][tipo][periodo] = valor
        data["realizacoes"][tipo][periodo]["updated_at"] = datetime.now().isoformat()
        
        self.save_budget_data(data)
    
    def calculate_performance(self, df: pd.DataFrame) -> Dict:
        """Calcula performance baseada nos dados reais"""
        if df.empty:
            return {}
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Performance mensal atual
        df_current_month = df[
            (df['ano'] == current_year) & 
            (df['mes'] == current_month)
        ]
        
        # Performance anual
        df_current_year = df[df['ano'] == current_year]
        
        performance = {
            "mensal_atual": {
                "containers": df_current_month['qtd_container'].sum(),
                "operacoes": len(df_current_month),
                "clientes_unicos": df_current_month['cliente'].nunique() if 'cliente' in df_current_month.columns else 0
            },
            "anual": {
                "containers": df_current_year['qtd_container'].sum(),
                "operacoes": len(df_current_year),
                "clientes_unicos": df_current_year['cliente'].nunique() if 'cliente' in df_current_year.columns else 0
            },
            "por_operacao": {}
        }
        
        # Performance por tipo de operação
        if 'tipo_operacao' in df_current_year.columns:
            for operacao in df_current_year['tipo_operacao'].unique():
                df_op = df_current_year[df_current_year['tipo_operacao'] == operacao]
                performance["por_operacao"][operacao] = {
                    "containers": df_op['qtd_container'].sum(),
                    "operacoes": len(df_op)
                }
        
        return performance
    
    def get_budget_vs_actual(self, df: pd.DataFrame) -> Dict:
        """Compara budget vs realizado"""
        budget_data = self.load_budget_data()
        performance = self.calculate_performance(df)
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        month_key = f"{current_year}-{current_month:02d}"
        
        comparison = {
            "anual": {},
            "mensal": {},
            "por_operacao": {}
        }
        
        # Comparação anual
        if str(current_year) in budget_data.get("metas_anuais", {}):
            meta_anual = budget_data["metas_anuais"][str(current_year)]
            real_anual = performance.get("anual", {})
            
            comparison["anual"] = {
                "containers": {
                    "meta": meta_anual.get("containers_total", 0),
                    "realizado": real_anual.get("containers", 0),
                    "percentual": self._calculate_percentage(
                        real_anual.get("containers", 0), 
                        meta_anual.get("containers_total", 0)
                    )
                }
            }
        
        # Comparação mensal
        if month_key in budget_data.get("metas_mensais", {}):
            meta_mensal = budget_data["metas_mensais"][month_key]
            real_mensal = performance.get("mensal_atual", {})
            
            comparison["mensal"] = {
                "containers": {
                    "meta": meta_mensal.get("containers", 0),
                    "realizado": real_mensal.get("containers", 0),
                    "percentual": self._calculate_percentage(
                        real_mensal.get("containers", 0), 
                        meta_mensal.get("containers", 0)
                    )
                }
            }
        
        return comparison
    
    def _calculate_percentage(self, actual: float, target: float) -> float:
        """Calcula percentual de atingimento"""
        if target == 0:
            return 0
        return (actual / target) * 100
    
    def generate_budget_insights(self, df: pd.DataFrame) -> List[str]:
        """Gera insights baseados no budget"""
        comparison = self.get_budget_vs_actual(df)
        insights = []
        
        # Insights anuais
        if "anual" in comparison and "containers" in comparison["anual"]:
            perc_anual = comparison["anual"]["containers"]["percentual"]
            if perc_anual >= 100:
                insights.append(f"🎯 Meta anual de containers ATINGIDA! ({perc_anual:.1f}%)")
            elif perc_anual >= 80:
                insights.append(f"📈 Boa performance anual: {perc_anual:.1f}% da meta atingida")
            elif perc_anual >= 50:
                insights.append(f"⚠️ Performance anual moderada: {perc_anual:.1f}% da meta")
            else:
                insights.append(f"🚨 Performance anual baixa: {perc_anual:.1f}% da meta")
        
        # Insights mensais
        if "mensal" in comparison and "containers" in comparison["mensal"]:
            perc_mensal = comparison["mensal"]["containers"]["percentual"]
            if perc_mensal >= 100:
                insights.append(f"🎯 Meta mensal de containers ATINGIDA! ({perc_mensal:.1f}%)")
            elif perc_mensal >= 80:
                insights.append(f"📈 Boa performance mensal: {perc_mensal:.1f}% da meta")
            else:
                insights.append(f"⚠️ Meta mensal: {perc_mensal:.1f}% atingida")
        
        return insights
    
    def get_opportunities(self, df: pd.DataFrame) -> List[Dict]:
        """Identifica oportunidades comerciais"""
        if df.empty:
            return []
        
        opportunities = []
        
        # Clientes com potencial de crescimento
        if 'cliente' in df.columns:
            client_performance = df.groupby('cliente')['qtd_container'].agg(['sum', 'count']).reset_index()
            client_performance.columns = ['cliente', 'total_containers', 'num_operacoes']
            
            # Clientes com alta frequência mas baixo volume
            high_freq_low_vol = client_performance[
                (client_performance['num_operacoes'] >= 5) & 
                (client_performance['total_containers'] < client_performance['total_containers'].median())
            ]
            
            for _, row in high_freq_low_vol.iterrows():
                opportunities.append({
                    "tipo": "upsell",
                    "cliente": row['cliente'],
                    "descricao": f"Cliente com {row['num_operacoes']} operações mas volume baixo ({row['total_containers']} containers)",
                    "potencial": "Alto"
                })
        
        # Análise sazonal
        if 'mes' in df.columns:
            monthly_volume = df.groupby('mes')['qtd_container'].sum()
            avg_volume = monthly_volume.mean()
            
            for mes, volume in monthly_volume.items():
                if volume < avg_volume * 0.7:  # 30% abaixo da média
                    opportunities.append({
                        "tipo": "sazonalidade",
                        "periodo": f"Mês {mes}",
                        "descricao": f"Volume baixo no mês {mes} ({volume:.0f} vs média {avg_volume:.0f})",
                        "potencial": "Médio"
                    })
        
        return opportunities[:10]  # Limitar a 10 oportunidades

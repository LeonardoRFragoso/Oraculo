"""
Módulo responsável pela análise avançada dos dados
"""
import pandas as pd
from .config import ANALISE_CONFIG

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
        "minimo": df[coluna].min(),
        "maximo": df[coluna].max(),
        "quartis": df[coluna].quantile([0.25, 0.75]).to_dict()
    }
    return stats

def gerar_insights(df, filtros):
    """Gera insights relevantes com base nos dados filtrados"""
    if df.empty:
        return []
    
    insights = []
    
    # Análise de volume
    total_containers = df["qtd_container"].sum()
    media_mensal = df.groupby("ano_mes")["qtd_container"].sum().mean()
    
    insights.append(f"Total de containers: {total_containers:,.0f}")
    insights.append(f"Média mensal: {media_mensal:,.0f} containers")
    
    # Análise de tendência
    tendencia = analisar_tendencias(df, "qtd_container")
    if tendencia:
        insights.append(f"Tendência {tendencia['tendencia']} com variação de {tendencia['variacao_total']:.1f}%")
        insights.append(f"Pico de {tendencia['pico']:,.0f} containers")
    
    # Análise por tipo de operação
    if "Categoria" in df.columns:
        por_categoria = df.groupby("Categoria")["qtd_container"].sum()
        for cat, total in por_categoria.items():
            insights.append(f"{cat}: {total:,.0f} containers ({(total/total_containers*100):.1f}%)")
    
    # Análise temporal
    if "ano_mes" in df.columns:
        ultimos_meses = df.groupby("ano_mes")["qtd_container"].sum().sort_index()
        if not ultimos_meses.empty:
            ultimo_mes = ultimos_meses.index[-1]
            mes_anterior = ultimos_meses.index[-2] if len(ultimos_meses) > 1 else None
            
            if mes_anterior:
                variacao_mes = ((ultimos_meses.iloc[-1] / ultimos_meses.iloc[-2]) - 1) * 100
                insights.append(f"Variação em relação ao mês anterior: {variacao_mes:+.1f}%")
    
    return insights

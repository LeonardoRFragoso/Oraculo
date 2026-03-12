"""
Módulo responsável por aplicar filtros aos dados
"""
import pandas as pd
from datetime import datetime
from .data_processing import normalize_text

def aplicar_filtros(df, filtros):
    """Aplica os filtros ao DataFrame"""
    if not filtros or df.empty:
        return df
    
    df_filtrado = df.copy()
    
    # Filtrar por categoria (importação/exportação)
    if filtros.get('categoria'):
        df_filtrado = df_filtrado.loc[df_filtrado['Categoria'].str.lower() == filtros['categoria'].lower()]
    
    # Filtrar por cliente
    if filtros.get('cliente'):
        mask = False
        colunas_cliente = [
            'CONSIGNATARIO FINAL', 'CONSIGNATÁRIO', 'NOME IMPORTADOR',
            'NOME EXPORTADOR', 'DESTINATÁRIO', 'REMETENTE'
        ]
        for col in colunas_cliente:
            if col in df_filtrado.columns:
                mask |= df_filtrado[col].str.lower() == filtros['cliente'].lower()
        df_filtrado = df_filtrado.loc[mask]
    
    # Filtrar por porto
    if filtros.get('porto'):
        mask = False
        colunas_porto = [col for col in df_filtrado.columns if 'porto' in col.lower()]
        for col in colunas_porto:
            if df_filtrado[col].dtype == 'object':
                mask |= df_filtrado[col].str.lower() == filtros['porto'].lower()
        df_filtrado = df_filtrado.loc[mask]
    
    # Filtrar por armador
    if filtros.get('armador'):
        df_filtrado = df_filtrado.loc[df_filtrado['ARMADOR'].str.lower() == filtros['armador'].lower()]
    
    # Filtrar por ano
    if filtros.get('ano'):
        df_filtrado = df_filtrado.loc[df_filtrado['ano'] == filtros['ano']]
    
    # Filtrar por mês
    if filtros.get('mes'):
        df_filtrado = df_filtrado.loc[df_filtrado['mes'] == filtros['mes']]
    
    # Filtrar por intervalo de datas
    if filtros.get('data_inicio') and filtros.get('data_fim'):
        df_filtrado = df_filtrado.loc[
            (df_filtrado['ANO/MÊS'] >= filtros['data_inicio']) &
            (df_filtrado['ANO/MÊS'] <= filtros['data_fim'])
        ]
    
    return df_filtrado

def filtrar_por_periodo(df, inicio, fim):
    """Filtra o DataFrame por um período específico"""
    if df.empty:
        return df
    
    # Converter datas para datetime se necessário
    inicio = pd.to_datetime(inicio)
    fim = pd.to_datetime(fim)
    
    # Identificar colunas de data
    colunas_data = [col for col in df.columns if 'data' in col.lower()]
    
    # Tentar filtrar por cada coluna de data até encontrar uma válida
    for col in colunas_data:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return df[
                (df[col] >= inicio) &
                (df[col] <= fim)
            ]
    
    # Se não encontrou coluna de data válida, tentar por ano/mês
    if 'ano' in df.columns and 'mes' in df.columns:
        mask = (
            ((df['ano'] == inicio.year) & (df['mes'] >= inicio.month)) |
            ((df['ano'] == fim.year) & (df['mes'] <= fim.month)) |
            ((df['ano'] > inicio.year) & (df['ano'] < fim.year))
        )
        return df[mask]
    
    return df

def top_n_by_column(df, column, n=10, sort_by=None):
    """Retorna os top N valores de uma coluna, ordenados por outra coluna opcional"""
    if df.empty or column not in df.columns:
        return pd.DataFrame()
    
    if sort_by is None:
        # Se não especificou coluna para ordenar, usar contagem
        return df[column].value_counts().head(n)
    
    # Agrupar por coluna e somar a coluna de ordenação
    grouped = df.groupby(column)[sort_by].sum().sort_values(ascending=False)
    return grouped.head(n)

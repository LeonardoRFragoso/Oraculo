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
    
    # Filtrar por cliente
    if 'cliente' in filtros:
        cliente = normalize_text(filtros['cliente'])
        mask = pd.Series(False, index=df.index)
        
        # Verificar em todas as colunas de cliente
        colunas_cliente = [
            'CONSIGNATARIO FINAL', 'CONSIGNATÁRIO', 'NOME IMPORTADOR',
            'NOME EXPORTADOR', 'DESTINATÁRIO', 'REMETENTE'
        ]
        
        for col in colunas_cliente:
            if col in df.columns:
                mask |= df[col].fillna('').str.contains(cliente, case=False, na=False)
        
        df_filtrado = df_filtrado[mask]
    
    # Filtrar por porto
    if 'porto' in filtros:
        porto = normalize_text(filtros['porto'])
        mask = pd.Series(False, index=df.index)
        
        # Verificar em todas as colunas de porto
        colunas_porto = [col for col in df.columns if 'porto' in col.lower()]
        for col in colunas_porto:
            if df[col].dtype == 'object':
                mask |= df[col].fillna('').str.contains(porto, case=False, na=False)
        
        df_filtrado = df_filtrado[mask]
    
    # Filtrar por ano
    if 'ano' in filtros:
        ano = int(filtros['ano'])
        df_filtrado = df_filtrado[df_filtrado['ano'] == ano]
    
    # Filtrar por mês
    if 'mes' in filtros:
        mes = int(filtros['mes'])
        df_filtrado = df_filtrado[df_filtrado['mes'] == mes]
    
    # Filtrar por categoria (importação/exportação)
    if 'categoria' in filtros:
        categoria = normalize_text(filtros['categoria'])
        df_filtrado = df_filtrado[df_filtrado['Categoria'].str.contains(categoria, case=False, na=False)]
    
    # Filtrar por armador
    if 'armador' in filtros:
        armador = normalize_text(filtros['armador'])
        df_filtrado = df_filtrado[df_filtrado['ARMADOR'].str.contains(armador, case=False, na=False)]
    
    # Filtrar por período específico
    if 'data_inicio' in filtros and 'data_fim' in filtros:
        data_inicio = pd.to_datetime(filtros['data_inicio'])
        data_fim = pd.to_datetime(filtros['data_fim'])
        
        # Tentar diferentes colunas de data
        colunas_data = [col for col in df.columns if 'data' in col.lower()]
        for col in colunas_data:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df_filtrado = df_filtrado[
                    (df_filtrado[col] >= data_inicio) &
                    (df_filtrado[col] <= data_fim)
                ]
                break
    
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

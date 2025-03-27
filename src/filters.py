"""
Módulo responsável por aplicar filtros aos dados
"""
import pandas as pd
from datetime import datetime
from .config import PORTO_MAPPING, CLIENTE_MAPPING

def aplicar_filtros(df, filtros):
    """Aplica filtros ao DataFrame com base nos critérios fornecidos"""
    if df.empty or not filtros:
        return df
    
    df_filtrado = df.copy()
    
    # Filtrar por ano
    if filtros.get('ano'):
        colunas_data = [col for col in df.columns if 'data' in col.lower()]
        if colunas_data:
            df_filtrado = df_filtrado[
                df_filtrado[colunas_data[0]].dt.year == filtros['ano']
            ]
    
    # Filtrar por mês
    if filtros.get('mes'):
        colunas_data = [col for col in df.columns if 'data' in col.lower()]
        if colunas_data:
            df_filtrado = df_filtrado[
                df_filtrado[colunas_data[0]].dt.month == filtros['mes']
            ]
    
    # Filtrar por porto
    if filtros.get('porto'):
        porto = str(filtros['porto']).lower()
        colunas_porto = []
        
        # Obter todas as colunas de porto possíveis
        for tipo in PORTO_MAPPING.values():
            colunas_porto.extend([col.lower() for col in tipo])
        
        # Remover duplicatas
        colunas_porto = list(set(colunas_porto))
        
        # Criar máscara para filtrar por porto em qualquer coluna
        mascara_porto = pd.Series(False, index=df_filtrado.index)
        for col in df_filtrado.columns:
            if col.lower() in colunas_porto:
                mascara_porto |= df_filtrado[col].astype(str).str.lower() == porto
        
        df_filtrado = df_filtrado[mascara_porto]
    
    # Filtrar por cliente
    if filtros.get('cliente'):
        cliente = str(filtros['cliente']).lower()
        colunas_cliente = []
        
        # Obter todas as colunas de cliente possíveis
        for tipo in CLIENTE_MAPPING.values():
            colunas_cliente.extend([col.lower() for col in tipo])
        
        # Remover duplicatas
        colunas_cliente = list(set(colunas_cliente))
        
        # Criar máscara para filtrar por cliente em qualquer coluna
        mascara_cliente = pd.Series(False, index=df_filtrado.index)
        for col in df_filtrado.columns:
            if col.lower() in colunas_cliente:
                mascara_cliente |= df_filtrado[col].astype(str).str.lower() == cliente
        
        df_filtrado = df_filtrado[mascara_cliente]
    
    # Filtrar por período relativo
    if filtros.get('periodo_relativo'):
        hoje = datetime.now()
        colunas_data = [col for col in df.columns if 'data' in col.lower()]
        
        if colunas_data:
            coluna_data = colunas_data[0]
            if filtros['periodo_relativo'] == 'ultimo':
                # Último mês completo
                ultimo_mes = hoje.replace(day=1).replace(hour=0, minute=0, second=0, microsecond=0)
                df_filtrado = df_filtrado[
                    df_filtrado[coluna_data] < ultimo_mes
                ]
            elif filtros['periodo_relativo'] == 'atual':
                # Mês atual
                inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                df_filtrado = df_filtrado[
                    df_filtrado[coluna_data] >= inicio_mes
                ]
    
    return df_filtrado

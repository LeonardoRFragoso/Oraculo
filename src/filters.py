"""
Módulo responsável por aplicar filtros aos dados
"""
import pandas as pd
from datetime import datetime
from .config import PORTO_MAPPING, CLIENTE_MAPPING
from .data_processing import normalize_text

def encontrar_colunas_porto(df, tipo_porto=None):
    """
    Encontra todas as colunas de porto disponíveis no DataFrame.
    Se tipo_porto for especificado, retorna apenas as colunas daquele tipo.
    """
    colunas_porto = []
    
    # Se tipo_porto não for especificado, buscar em todas as categorias
    categorias = [tipo_porto] if tipo_porto else PORTO_MAPPING.keys()
    
    for categoria in categorias:
        for coluna in PORTO_MAPPING[categoria]:
            if coluna in df.columns:
                colunas_porto.append(coluna)
    
    return list(set(colunas_porto))  # Remover duplicatas

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
        porto = normalize_text(str(filtros['porto']))
        colunas_porto = encontrar_colunas_porto(df_filtrado)
        
        # Criar máscara para filtrar por porto em qualquer coluna
        mascara_porto = pd.Series(False, index=df_filtrado.index)
        for col in colunas_porto:
            mascara_porto |= df_filtrado[col].apply(normalize_text) == porto
        
        df_filtrado = df_filtrado[mascara_porto]
    
    # Filtrar por cliente
    if filtros.get('cliente'):
        cliente = normalize_text(str(filtros['cliente']))
        colunas_cliente = []
        
        # Obter todas as colunas de cliente possíveis
        for tipo in CLIENTE_MAPPING.values():
            colunas_cliente.extend(tipo)
        
        # Remover duplicatas
        colunas_cliente = list(set(colunas_cliente))
        
        # Criar máscara para filtrar por cliente em qualquer coluna
        mascara_cliente = pd.Series(False, index=df_filtrado.index)
        for col in colunas_cliente:
            if col in df_filtrado.columns:
                mascara_cliente |= df_filtrado[col].apply(normalize_text) == cliente
        
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

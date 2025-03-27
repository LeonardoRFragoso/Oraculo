"""
Módulo responsável pelo processamento e normalização dos dados
"""
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime

def normalize_text(text):
    """Normaliza texto removendo acentos e convertendo para minúsculo"""
    if isinstance(text, str):
        return unicodedata.normalize('NFKD', text).encode('ascii', errors='ignore').decode('utf-8').lower().strip()
    return text

def detectar_formato_data(serie):
    """Detecta o formato da data baseado em uma amostra dos dados"""
    amostra = serie.dropna().head(100)  # Pegar uma amostra para análise
    
    # Tentar diferentes formatos comuns
    formatos = [
        ('%d/%m/%Y', True),  # BR - dia/mês/ano
        ('%Y-%m-%d', False), # ISO - ano-mês-dia
        ('%m/%d/%Y', False), # US - mês/dia/ano
        ('%Y/%m/%d', False)  # ISO alternativo
    ]
    
    for fmt, dayfirst in formatos:
        try:
            # Tentar converter a amostra
            pd.to_datetime(amostra, format=fmt)
            return fmt, dayfirst
        except:
            continue
    
    # Se nenhum formato específico funcionar, deixar o pandas detectar
    return None, False

def processar_datas(df):
    """Processa todas as colunas de data do DataFrame"""
    df = df.copy()
    colunas_data = [col for col in df.columns if 'data' in col.lower()]
    
    for col in colunas_data:
        if not df[col].isna().all():  # Ignorar colunas vazias
            formato, dayfirst = detectar_formato_data(df[col])
            if formato:
                # Se detectou um formato específico, usar ele
                df[col] = pd.to_datetime(df[col], format=formato)
            else:
                # Caso contrário, deixar o pandas inferir
                df[col] = pd.to_datetime(df[col], dayfirst=False)
            
            # Adicionar colunas de ano e mês
            df['ano'] = df[col].dt.year
            df['mes'] = df[col].dt.month
    
    return df

def limpar_qtd_coluna(coluna):
    """Limpa e converte valores de quantidade para float"""
    def clean_value(val):
        if pd.isna(val):
            return 0
        if isinstance(val, (int, float)):
            return float(val)
        # Converter string para um formato padrão
        val = str(val).strip()
        val = val.replace(".", "").replace(",", ".")
        match = re.search(r'(\d+\.?\d*)', val)
        return float(match.group(1)) if match else 0
    return coluna.apply(clean_value)

def processar_dados(df):
    """Processa e limpa os dados do DataFrame"""
    if df.empty:
        return df
    
    # Normalizar nomes das colunas
    df.columns = [normalize_text(col) for col in df.columns]
    
    # Processar datas
    df = processar_datas(df)
    
    # Limpar e converter colunas de quantidade
    colunas_qtd = [col for col in df.columns if 'qtd' in col.lower() or 'quantidade' in col.lower()]
    for col in colunas_qtd:
        df[col] = limpar_qtd_coluna(df[col])
    
    # Processar colunas de texto
    colunas_texto = df.select_dtypes(include=['object']).columns
    for col in colunas_texto:
        df[col] = df[col].apply(normalize_text)
    
    return df

def unificar_contagem_containers(df, filtros=None):
    """Unifica a contagem de containers considerando diferentes colunas"""
    if df.empty:
        return 0
    
    # Identificar colunas de quantidade
    colunas_qtd = [col for col in df.columns if 'qtd' in col.lower() or 'quantidade' in col.lower()]
    
    if not colunas_qtd:
        return 0
    
    # Somar todas as colunas de quantidade
    total = 0
    for col in colunas_qtd:
        total += df[col].sum()
    
    return int(total)

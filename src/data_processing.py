"""
Módulo responsável pelo processamento e limpeza dos dados
"""
import re
import unicodedata
import pandas as pd
from .config import CATEGORIA_MAPPING, CLIENTE_MAPPING, PORTO_MAPPING

def normalize_text(text):
    """Normaliza texto removendo acentos e convertendo para minúsculas"""
    if isinstance(text, str):
        return unicodedata.normalize('NFKD', text).encode('ascii', errors='ignore').decode('utf-8').lower().strip()
    return text

def limpar_qtd_coluna(coluna):
    """Limpa e padroniza colunas de quantidade"""
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
    
    # Processar colunas de quantidade
    colunas_qtd = [col for col in df.columns if 'qtd' in col.lower() or 'quantidade' in col.lower()]
    for col in colunas_qtd:
        df[col] = limpar_qtd_coluna(df[col])
    
    # Processar colunas de data
    colunas_data = [col for col in df.columns if 'data' in col.lower()]
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Processar colunas de texto
    colunas_texto = df.select_dtypes(include=['object']).columns
    for col in colunas_texto:
        df[col] = df[col].apply(normalize_text)
    
    return df

def unificar_contagem_containers(df, filtros):
    """Unifica a contagem de containers com base nos filtros aplicados"""
    if df.empty:
        return 0
        
    # Identificar colunas de quantidade
    colunas_qtd = [col for col in df.columns if 'qtd' in col.lower() or 'quantidade' in col.lower()]
    
    if not colunas_qtd:
        return 0
        
    # Somar todas as colunas de quantidade
    total = 0
    for col in colunas_qtd:
        total += df[col].fillna(0).sum()
    
    return total

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

def limpar_qtd_coluna(coluna):
    """Limpa e converte uma coluna de quantidade para float"""
    def clean_value(val):
        try:
            if pd.isna(val):
                return 0
            if isinstance(val, (int, float)):
                return float(val)
            # Converter string para um formato padrão
            val = str(val).strip()
            val = val.replace(".", "").replace(",", ".")
            # Remover caracteres não numéricos exceto ponto decimal
            val = ''.join(c for c in val if c.isdigit() or c == '.')
            # Se não houver dígitos, retornar 0
            if not any(c.isdigit() for c in val):
                return 0
            # Se houver múltiplos pontos, manter apenas o último
            if val.count('.') > 1:
                parts = val.split('.')
                val = ''.join(parts[:-1]) + '.' + parts[-1]
            return float(val) if val else 0
        except Exception as e:
            print(f"Erro ao converter valor '{val}': {str(e)}")
            return 0
    return coluna.apply(clean_value)

def detectar_formato_data(serie):
    """Detecta o formato da data baseado em uma amostra dos dados"""
    amostra = serie.dropna().head(100)
    
    formatos = [
        ('%d/%m/%Y', True),
        ('%Y-%m-%d', False),
        ('%m/%d/%Y', False),
        ('%Y/%m/%d', False),
        ('%d-%m-%Y', True),
        ('%Y/%m', False)  # Para coluna ANO/MÊS
    ]
    
    for fmt, dayfirst in formatos:
        try:
            pd.to_datetime(amostra, format=fmt)
            return fmt, dayfirst
        except:
            continue
    
    return None, False

def processar_datas(df):
    """Processa todas as colunas de data do DataFrame"""
    df = df.copy()
    
    # Processar coluna ANO/MÊS
    if 'ANO/MÊS' in df.columns:
        try:
            # Converter para string primeiro para garantir o formato correto
            df['ANO/MÊS'] = df['ANO/MÊS'].astype(str).str.zfill(6)
            df['ANO/MÊS'] = pd.to_datetime(df['ANO/MÊS'], format='%Y%m')
            df['ano'] = df['ANO/MÊS'].dt.year
            df['mes'] = df['ANO/MÊS'].dt.month
        except:
            pass
    
    # Processar outras colunas de data
    colunas_data = ['DATA CONSULTA', 'DATA DE EMBARQUE', 'DATA EMBARQUE', 'DATA_EXTRACAO', 'ETA', 'ETS', 'SAÍDA PORTO']
    for col in colunas_data:
        if col in df.columns and not df[col].isna().all():
            formato, dayfirst = detectar_formato_data(df[col])
            if formato:
                df[col] = pd.to_datetime(df[col], format=formato)
            else:
                df[col] = pd.to_datetime(df[col], dayfirst=dayfirst)
            
            if 'ano' not in df.columns:
                df['ano'] = df[col].dt.year
            if 'mes' not in df.columns:
                df['mes'] = df[col].dt.month
    
    return df

def unificar_contagem_containers(df, filtros=None):
    """Unifica a contagem de containers considerando diferentes colunas"""
    if df.empty:
        return 0
    
    # Lista de colunas que podem conter contagens
    colunas_container = [
        'QTDE CONTAINER', 'QTDE CONTEINER', 'QUANTIDADE TEUS',
        'C20', 'C40', 'QUANTIDADE C20', 'QUANTIDADE C40',
        'TEUS', 'QTDE FCL'
    ]
    
    # Filtrar apenas colunas que existem no DataFrame
    colunas_existentes = [col for col in colunas_container if col in df.columns]
    
    if not colunas_existentes:
        return 0
    
    # Priorizar QTDE CONTAINER ou QTDE CONTEINER
    for col in ['QTDE CONTAINER', 'QTDE CONTEINER']:
        if col in colunas_existentes:
            return int(df[col].fillna(0).astype(str).str.replace(',', '.').astype(float).sum())
    
    # Se não encontrou as colunas principais, somar C20 e C40
    total = 0
    if 'C20' in colunas_existentes:
        total += df['C20'].fillna(0).astype(str).str.replace(',', '.').astype(float).sum()
    if 'C40' in colunas_existentes:
        total += df['C40'].fillna(0).astype(str).str.replace(',', '.').astype(float).sum() * 2
    
    # Se ainda não encontrou, tentar QUANTIDADE C20 e C40
    if total == 0:
        if 'QUANTIDADE C20' in colunas_existentes:
            total += df['QUANTIDADE C20'].fillna(0).astype(str).str.replace(',', '.').astype(float).sum()
        if 'QUANTIDADE C40' in colunas_existentes:
            total += df['QUANTIDADE C40'].fillna(0).astype(str).str.replace(',', '.').astype(float).sum() * 2
    
    # Se ainda não encontrou, usar QUANTIDADE TEUS ou TEUS
    if total == 0:
        for col in ['QUANTIDADE TEUS', 'TEUS']:
            if col in colunas_existentes:
                total = df[col].fillna(0).astype(str).str.replace(',', '.').astype(float).sum()
                break
    
    return int(total)

def processar_dados(df):
    """Processa e limpa os dados do DataFrame"""
    if df.empty:
        return df
    
    # Criar cópia para não modificar o original
    df = df.copy()
    
    # Processar datas
    df = processar_datas(df)
    
    # Normalizar textos
    colunas_texto = df.select_dtypes(include=['object']).columns
    for col in colunas_texto:
        df[col] = df[col].apply(normalize_text)
    
    # Unificar colunas de porto
    colunas_porto = [col for col in df.columns if 'porto' in col.lower()]
    for col in colunas_porto:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(normalize_text)
    
    # Unificar colunas de cliente/consignatário
    colunas_cliente = [
        'CONSIGNATARIO FINAL', 'CONSIGNATÁRIO', 'NOME IMPORTADOR',
        'NOME EXPORTADOR', 'DESTINATÁRIO', 'REMETENTE'
    ]
    for col in colunas_cliente:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)
    
    # Converter valores numéricos
    colunas_numericas = [
        'VOLUMES', 'VOLUME (M³)', 'PESO BRUTO',
        'QTDE CONTAINER', 'QTDE CONTEINER', 'QUANTIDADE TEUS',
        'C20', 'C40', 'QUANTIDADE C20', 'QUANTIDADE C40',
        'TEUS', 'QTDE FCL', 'QTDE VEÍCULOS', 'QUANTIDADE VEICULOS'
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = limpar_qtd_coluna(df[col])
    
    return df

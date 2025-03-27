"""
Módulo responsável por interpretar as perguntas do usuário
"""
import re
from datetime import datetime
from .data_processing import normalize_text
from .config import CATEGORIA_MAPPING, CLIENTE_MAPPING, PORTO_MAPPING

def interpretar_pergunta(pergunta, df):
    """Interpreta a pergunta do usuário e extrai filtros relevantes"""
    filtros = {
        'operacao': None,
        'ano': None,
        'mes': None,
        'periodo_relativo': None,
        'porto': None,
        'cliente': None
    }
    
    # Normalizar texto da pergunta
    pergunta_norm = normalize_text(pergunta)
    
    # Detectar tipo de operação
    for operacao, keywords in CATEGORIA_MAPPING.items():
        if any(keyword in pergunta_norm for keyword in keywords):
            filtros['operacao'] = operacao
            break
    
    # Detectar ano
    match_ano = re.search(r'\b(20\d{2})\b', pergunta)
    if match_ano:
        filtros['ano'] = int(match_ano.group(1))
    
    # Detectar mês
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    for mes, num in meses.items():
        if mes in pergunta_norm:
            filtros['mes'] = num
            break
    
    # Detectar período relativo
    if 'último' in pergunta_norm or 'ultim' in pergunta_norm:
        filtros['periodo_relativo'] = 'ultimo'
    elif 'atual' in pergunta_norm:
        filtros['periodo_relativo'] = 'atual'
    
    # Detectar porto
    for operacao, colunas_porto in PORTO_MAPPING.items():
        for coluna in colunas_porto:
            if coluna.lower() in df.columns:
                portos_unicos = df[coluna].dropna().unique()
                for porto in portos_unicos:
                    if str(porto).lower() in pergunta_norm:
                        filtros['porto'] = porto
                        break
                if filtros['porto']:
                    break
        if filtros['porto']:
            break
    
    # Detectar cliente
    for operacao, colunas_cliente in CLIENTE_MAPPING.items():
        for coluna in colunas_cliente:
            if coluna.lower() in df.columns:
                clientes_unicos = df[coluna].dropna().unique()
                for cliente in clientes_unicos:
                    if str(cliente).lower() in pergunta_norm:
                        filtros['cliente'] = cliente
                        break
                if filtros['cliente']:
                    break
        if filtros['cliente']:
            break
    
    return filtros

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
    # Primeiro tenta encontrar o porto completo (ex: "porto de santos")
    match_porto = re.search(r'porto\s+(?:de\s+)?([a-zA-Z\s]+?)(?:\s+em|\s+no|\s+na|\s+para|\s+e|$)', pergunta_norm)
    if match_porto:
        porto = match_porto.group(1).strip()
        # Se o porto for muito genérico (ex: "porto de origem"), não incluir
        if porto not in ['origem', 'destino', 'embarque', 'descarga']:
            filtros['porto'] = porto
    
    # Se não encontrou porto completo, procura apenas o nome
    if 'porto' not in filtros:
        portos_conhecidos = ['santos', 'paranagua', 'rio grande', 'itajai', 'vitoria']
        for porto in portos_conhecidos:
            if porto in pergunta_norm:
                filtros['porto'] = porto
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

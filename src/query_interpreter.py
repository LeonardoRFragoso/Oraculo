"""
Módulo responsável por interpretar perguntas e extrair filtros
"""
import re
from datetime import datetime, timedelta
from .data_processing import normalize_text

def detectar_cliente(pergunta, df):
    """Detecta menções a clientes na pergunta"""
    if df.empty:
        return None
    
    pergunta = normalize_text(pergunta)
    
    # Lista de colunas que podem conter nomes de clientes
    colunas_cliente = [
        'CONSIGNATARIO FINAL', 'CONSIGNATÁRIO', 'NOME IMPORTADOR',
        'NOME EXPORTADOR', 'DESTINATÁRIO', 'REMETENTE'
    ]
    
    # Buscar o cliente mais próximo na pergunta
    melhor_match = None
    maior_similaridade = 0
    
    for col in colunas_cliente:
        if col in df.columns:
            clientes = df[col].dropna().unique()
            for cliente in clientes:
                cliente_norm = normalize_text(str(cliente))
                if cliente_norm in pergunta:
                    # Se encontrou match exato, retornar imediatamente
                    return cliente_norm
                
                # Calcular similaridade por palavras em comum
                palavras_cliente = set(cliente_norm.split())
                palavras_pergunta = set(pergunta.split())
                palavras_comuns = palavras_cliente & palavras_pergunta
                
                if palavras_comuns:
                    similaridade = len(palavras_comuns) / len(palavras_cliente)
                    if similaridade > maior_similaridade:
                        maior_similaridade = similaridade
                        melhor_match = cliente_norm
    
    return melhor_match if maior_similaridade > 0.5 else None

def detectar_porto(pergunta, df):
    """Detecta menções a portos na pergunta"""
    if df.empty:
        return None
    
    pergunta = normalize_text(pergunta)
    
    # Buscar em todas as colunas que contêm "porto"
    colunas_porto = [col for col in df.columns if 'porto' in col.lower()]
    
    for col in colunas_porto:
        if df[col].dtype == 'object':
            portos = df[col].dropna().unique()
            for porto in portos:
                porto_norm = normalize_text(str(porto))
                if porto_norm in pergunta:
                    return porto_norm
    
    return None

def detectar_periodo(pergunta):
    """Detecta menções a períodos na pergunta"""
    pergunta = normalize_text(pergunta)
    
    # Detectar ano
    anos = re.findall(r'\b20\d{2}\b', pergunta)
    if anos:
        ano = int(anos[0])
    else:
        ano = None
    
    # Detectar mês
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    
    mes = None
    for nome_mes, num_mes in meses.items():
        if nome_mes in pergunta:
            mes = num_mes
            break
    
    return ano, mes

def detectar_categoria(pergunta):
    """Detecta se a pergunta é sobre importação ou exportação"""
    pergunta = normalize_text(pergunta)
    
    if 'importa' in pergunta:
        return 'importacao'
    elif 'exporta' in pergunta:
        return 'exportacao'
    
    return None

def extrair_filtros(pergunta, df):
    """Extrai filtros da pergunta"""
    filtros = {}
    
    # Detectar cliente
    cliente = detectar_cliente(pergunta, df)
    if cliente:
        filtros['cliente'] = cliente
    
    # Detectar porto
    porto = detectar_porto(pergunta, df)
    if porto:
        filtros['porto'] = porto
    
    # Detectar período
    ano, mes = detectar_periodo(pergunta)
    if ano:
        filtros['ano'] = ano
    if mes:
        filtros['mes'] = mes
    
    # Detectar categoria (importação/exportação)
    categoria = detectar_categoria(pergunta)
    if categoria:
        filtros['categoria'] = categoria
    
    # Detectar armador
    if 'armador' in normalize_text(pergunta) and 'ARMADOR' in df.columns:
        filtros['tipo_analise'] = 'armador'
    
    return filtros

def interpretar_pergunta(pergunta, df):
    """Interpreta a pergunta e retorna os filtros apropriados"""
    if not isinstance(pergunta, str) or df.empty:
        return {}
    
    # Extrair filtros básicos
    filtros = extrair_filtros(pergunta, df)
    
    # Identificar tipo de análise
    pergunta = normalize_text(pergunta)
    
    if 'comparar' in pergunta or 'comparação' in pergunta:
        filtros['tipo_analise'] = 'comparacao'
    elif 'tendência' in pergunta or 'tendencia' in pergunta:
        filtros['tipo_analise'] = 'tendencia'
    elif 'ranking' in pergunta or 'principais' in pergunta or 'top' in pergunta:
        filtros['tipo_analise'] = 'ranking'
    elif 'total' in pergunta or 'quantidade' in pergunta or 'volume' in pergunta:
        filtros['tipo_analise'] = 'total'
    
    return filtros

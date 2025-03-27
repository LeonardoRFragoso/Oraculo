"""
Módulo responsável por interpretar perguntas e extrair filtros
"""
import re
from datetime import datetime
import pandas as pd
from .data_processing import normalize_text

def detectar_tipo_analise(pergunta):
    """Detecta o tipo de análise com base na pergunta"""
    pergunta = pergunta.lower()
    
    # Palavras-chave para cada tipo de análise
    keywords = {
        'comparacao': ['compare', 'comparar', 'diferença', 'variação', 'versus', 'vs'],
        'ranking': ['principais', 'ranking', 'top', 'maiores', 'ordenados', 'classificação'],
        'tendencia': ['tendência', 'tendencia', 'evolução', 'últimos meses', 'ultimos meses']
    }
    
    for tipo, palavras in keywords.items():
        if any(palavra in pergunta for palavra in palavras):
            return tipo
    
    return 'total'

def extrair_datas(pergunta):
    """Extrai datas da pergunta"""
    pergunta = pergunta.lower()
    
    # Mapear nomes de meses para números
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    
    # Extrair ano
    anos = re.findall(r'\b20\d{2}\b', pergunta)
    ano = int(anos[0]) if anos else None
    
    # Extrair mês
    mes = None
    for nome_mes, num_mes in meses.items():
        if nome_mes in pergunta:
            mes = num_mes
            break
    
    # Se encontrou ano e mês, criar data
    if ano and mes:
        return pd.to_datetime(f"{ano}-{mes:02d}-01")
    
    return None

def extrair_periodo_comparacao(pergunta):
    """Extrai período para comparação"""
    pergunta = pergunta.lower()
    
    # Tentar extrair duas datas
    datas = []
    palavras = pergunta.split()
    
    for i, palavra in enumerate(palavras):
        # Verificar se é uma referência a mês/ano
        if palavra in ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                      'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
                      'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set',
                      'out', 'nov', 'dez']:
            # Procurar por ano próximo
            for j in range(max(0, i-2), min(len(palavras), i+3)):
                if re.match(r'20\d{2}', palavras[j]):
                    data = extrair_datas(' '.join([palavra, palavras[j]]))
                    if data and data not in datas:
                        datas.append(data)
    
    if len(datas) >= 2:
        return min(datas), max(datas)
    
    # Se não encontrou duas datas, tentar extrair uma data e assumir mês anterior
    data = extrair_datas(pergunta)
    if data:
        data_anterior = data - pd.DateOffset(months=1)
        return data_anterior, data
    
    return None, None

def detectar_cliente(pergunta, df):
    """Detecta menção a cliente na pergunta"""
    if df.empty:
        return None
        
    pergunta = normalize_text(pergunta)
    
    # Lista de colunas que podem conter nomes de clientes
    colunas_cliente = [
        'CONSIGNATARIO FINAL', 'CONSIGNATÁRIO', 'NOME IMPORTADOR',
        'NOME EXPORTADOR', 'DESTINATÁRIO', 'REMETENTE'
    ]
    
    # Criar um conjunto com todos os clientes únicos
    clientes = set()
    for col in colunas_cliente:
        if col in df.columns:
            clientes.update(df[col].dropna().unique())
    
    # Normalizar nomes dos clientes
    clientes = {normalize_text(cliente) for cliente in clientes if isinstance(cliente, str)}
    
    # Procurar por cliente na pergunta
    for cliente in clientes:
        if cliente in pergunta:
            return cliente
    
    return None

def detectar_porto(pergunta, df):
    """Detecta menção a porto na pergunta"""
    if df.empty:
        return None
        
    pergunta = normalize_text(pergunta)
    
    # Lista de colunas que podem conter nomes de portos
    colunas_porto = [col for col in df.columns if 'porto' in col.lower()]
    
    # Criar um conjunto com todos os portos únicos
    portos = set()
    for col in colunas_porto:
        if df[col].dtype == 'object':
            portos.update(df[col].dropna().unique())
    
    # Normalizar nomes dos portos
    portos = {normalize_text(porto) for porto in portos if isinstance(porto, str)}
    
    # Procurar por porto na pergunta
    for porto in portos:
        if porto in pergunta:
            return porto
    
    return None

def extrair_filtros(pergunta, df):
    """Extrai filtros da pergunta"""
    filtros = {}
    
    # Detectar tipo de análise
    filtros['tipo_analise'] = detectar_tipo_analise(pergunta)
    
    # Extrair cliente
    cliente = detectar_cliente(pergunta, df)
    if cliente:
        filtros['cliente'] = cliente
    
    # Extrair porto
    porto = detectar_porto(pergunta, df)
    if porto:
        filtros['porto'] = porto
    
    # Extrair categoria (importação/exportação)
    if 'importação' in pergunta.lower() or 'importacao' in pergunta.lower():
        filtros['categoria'] = 'importação'
    elif 'exportação' in pergunta.lower() or 'exportacao' in pergunta.lower():
        filtros['categoria'] = 'exportação'
    
    # Extrair período
    if filtros['tipo_analise'] == 'comparacao':
        data_inicio, data_fim = extrair_periodo_comparacao(pergunta)
        if data_inicio and data_fim:
            filtros['data_inicio'] = data_inicio
            filtros['data_fim'] = data_fim
    else:
        data = extrair_datas(pergunta)
        if data:
            filtros['ano'] = data.year
            filtros['mes'] = data.month
    
    return filtros

def interpretar_pergunta(pergunta, df):
    """Interpreta a pergunta e retorna os filtros apropriados"""
    if not pergunta or df.empty:
        return {}
    
    return extrair_filtros(pergunta, df)

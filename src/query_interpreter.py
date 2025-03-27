"""
Módulo responsável por interpretar as perguntas do usuário
"""
import re
from datetime import datetime
from .data_processing import normalize_text
from .config import CATEGORIA_MAPPING, CLIENTE_MAPPING, PORTO_MAPPING

def detectar_cliente(pergunta, df):
    """Detecta menções a clientes na pergunta"""
    if df.empty:
        return None
        
    pergunta_norm = normalize_text(pergunta)
    
    # Obter todas as colunas de cliente
    colunas_cliente = []
    for tipo in CLIENTE_MAPPING.values():
        colunas_cliente.extend(tipo)
    
    # Remover duplicatas e manter apenas colunas existentes
    colunas_cliente = [col for col in set(colunas_cliente) if col in df.columns]
    
    # Se não houver colunas de cliente, retornar None
    if not colunas_cliente:
        return None
    
    # Criar um dicionário com todos os clientes normalizados
    clientes = {}
    for col in colunas_cliente:
        for cliente in df[col].dropna().unique():
            cliente_norm = normalize_text(str(cliente))
            if cliente_norm and len(cliente_norm) > 3:  # Ignorar valores muito curtos
                clientes[cliente_norm] = cliente
    
    # Procurar pelo cliente mais longo que corresponda à pergunta
    cliente_encontrado = None
    max_len = 0
    
    for cliente_norm, cliente_original in clientes.items():
        if cliente_norm in pergunta_norm and len(cliente_norm) > max_len:
            cliente_encontrado = cliente_original
            max_len = len(cliente_norm)
    
    return cliente_encontrado

def extrair_filtros(pergunta, df=None):
    """Extrai filtros da pergunta do usuário"""
    filtros = {}
    pergunta_norm = normalize_text(pergunta)
    
    # Extrair ano
    match_ano = re.search(r'(?:em|de|do ano|durante|para)\s+(\d{4})', pergunta_norm)
    if match_ano:
        filtros['ano'] = int(match_ano.group(1))
    
    # Extrair mês
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    for mes, num in meses.items():
        if mes in pergunta_norm:
            filtros['mes'] = num
            break
    
    # Extrair porto
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
    
    # Extrair cliente usando a função especializada
    if df is not None:
        cliente = detectar_cliente(pergunta, df)
        if cliente:
            filtros['cliente'] = cliente
    
    # Extrair período relativo
    if 'ultimo mes' in pergunta_norm or 'mes passado' in pergunta_norm:
        filtros['periodo_relativo'] = 'ultimo'
    elif 'mes atual' in pergunta_norm or 'este mes' in pergunta_norm:
        filtros['periodo_relativo'] = 'atual'
    
    # Detectar tipo de operação
    for operacao, keywords in CATEGORIA_MAPPING.items():
        if any(keyword in pergunta_norm for keyword in keywords):
            filtros['operacao'] = operacao
            break
    
    return filtros

def interpretar_pergunta(pergunta, df):
    """Interpreta a pergunta do usuário e extrai filtros relevantes"""
    return extrair_filtros(pergunta, df)

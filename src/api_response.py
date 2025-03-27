"""
Módulo responsável por gerar respostas às perguntas
"""
import pandas as pd
from .data_processing import unificar_contagem_containers
from .filters import aplicar_filtros, filtrar_por_periodo, top_n_by_column

def formatar_numero(n):
    """Formata um número para exibição"""
    return f"{int(n):,}".replace(",", ".")

def gerar_resposta_total(df_filtrado, filtros):
    """Gera resposta para perguntas sobre totais"""
    total = unificar_contagem_containers(df_filtrado)
    
    # Construir resposta
    resposta = f"O total de containers foi {formatar_numero(total)}"
    
    # Adicionar contexto temporal se disponível
    if 'ano' in filtros and 'mes' in filtros:
        resposta += f" em {filtros['mes']}/{filtros['ano']}"
    elif 'ano' in filtros:
        resposta += f" em {filtros['ano']}"
    elif 'mes' in filtros:
        resposta += f" no mês {filtros['mes']}"
    
    # Adicionar contexto de cliente
    if 'cliente' in filtros:
        resposta += f" para o cliente {filtros['cliente']}"
    
    # Adicionar contexto de porto
    if 'porto' in filtros:
        resposta += f" no porto de {filtros['porto']}"
    
    # Adicionar contexto de categoria
    if 'categoria' in filtros:
        resposta += f" em operações de {filtros['categoria']}"
    
    return resposta + "."

def gerar_resposta_comparacao(df, filtros):
    """Gera resposta para perguntas de comparação"""
    if 'ano' not in filtros or 'mes' not in filtros:
        return "Não foi possível identificar o período para comparação."
    
    # Comparar meses do mesmo ano
    ano = filtros['ano']
    mes1 = filtros['mes']
    mes2 = mes1 - 1 if mes1 > 1 else 12
    ano2 = ano if mes1 > 1 else ano - 1
    
    # Filtrar dados para cada período
    df1 = df[(df['ano'] == ano) & (df['mes'] == mes1)]
    df2 = df[(df['ano'] == ano2) & (df['mes'] == mes2)]
    
    # Calcular totais
    total1 = unificar_contagem_containers(df1)
    total2 = unificar_contagem_containers(df2)
    
    # Calcular variação
    if total2 > 0:
        variacao = ((total1 - total2) / total2) * 100
        tendencia = "aumento" if variacao > 0 else "redução"
        
        resposta = f"Comparação entre os períodos:\n"
        resposta += f"- {mes1}/{ano}: {formatar_numero(total1)} containers\n"
        resposta += f"- {mes2}/{ano2}: {formatar_numero(total2)} containers\n"
        resposta += f"\nHouve {tendencia} de {abs(variacao):.1f}% no volume de containers."
        
        return resposta
    
    return f"Não foi possível realizar a comparação devido à falta de dados no período anterior."

def gerar_resposta_ranking(df_filtrado, filtros):
    """Gera resposta para perguntas sobre ranking"""
    if df_filtrado.empty:
        return "Não foram encontrados dados para gerar o ranking."
    
    # Definir coluna para ranking
    if filtros.get('tipo_analise') == 'armador':
        coluna = 'ARMADOR'
    else:
        # Tentar encontrar a coluna mais apropriada
        colunas_possiveis = ['ARMADOR', 'CONSIGNATARIO FINAL', 'PORTO EMBARQUE']
        for col in colunas_possiveis:
            if col in df_filtrado.columns:
                coluna = col
                break
        else:
            return "Não foi possível identificar a coluna para gerar o ranking."
    
    # Gerar ranking
    ranking = top_n_by_column(df_filtrado, coluna, n=5)
    
    if ranking.empty:
        return "Não foram encontrados dados suficientes para gerar o ranking."
    
    # Formatar resposta
    resposta = f"Top 5 {coluna.lower()}s"
    if 'ano' in filtros:
        resposta += f" em {filtros['ano']}"
    if 'mes' in filtros:
        resposta += f" no mês {filtros['mes']}"
    if 'porto' in filtros:
        resposta += f" no porto de {filtros['porto']}"
    resposta += ":\n\n"
    
    for i, (nome, valor) in enumerate(ranking.items(), 1):
        resposta += f"{i}. {nome}: {formatar_numero(valor)} containers\n"
    
    return resposta

def responder_pergunta(pergunta, df, filtros):
    """Gera uma resposta para a pergunta com base nos filtros e dados"""
    if df.empty:
        return "Não há dados disponíveis para análise."
    
    # Aplicar filtros aos dados
    df_filtrado = aplicar_filtros(df, filtros)
    
    if df_filtrado.empty:
        return "Não foram encontrados dados que correspondam aos critérios da sua pergunta. Por favor, verifique se os filtros estão corretos."
    
    # Gerar resposta apropriada com base no tipo de análise
    tipo_analise = filtros.get('tipo_analise', 'total')
    
    if tipo_analise == 'comparacao':
        return gerar_resposta_comparacao(df, filtros)
    elif tipo_analise == 'ranking':
        return gerar_resposta_ranking(df_filtrado, filtros)
    else:  # total ou outros tipos
        return gerar_resposta_total(df_filtrado, filtros)

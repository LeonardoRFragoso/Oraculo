"""
Módulo responsável por gerar respostas às perguntas
"""
import pandas as pd
from .data_processing import unificar_contagem_containers
from .filters import aplicar_filtros, filtrar_por_periodo, top_n_by_column

def formatar_numero(n):
    """Formata um número para exibição"""
    return f"{int(n):,}".replace(",", ".")

def gerar_resposta_total(df, filtros):
    """Gera resposta para perguntas sobre totais"""
    total_containers = unificar_contagem_containers(df)
    
    # Construir resposta detalhada
    resposta = []
    
    # Adicionar informação sobre o período
    if filtros.get('ano') and filtros.get('mes'):
        periodo = f"em {filtros['mes']}/{filtros['ano']}"
    elif filtros.get('ano'):
        periodo = f"em {filtros['ano']}"
    else:
        periodo = "no período analisado"
    
    # Adicionar informação sobre o cliente
    if filtros.get('cliente'):
        resposta.append(f"O total de containers foi {total_containers} {periodo} para o cliente {filtros['cliente']}.")
    else:
        resposta.append(f"O total de containers foi {total_containers} {periodo}.")
    
    # Adicionar informação sobre categoria
    if filtros.get('categoria'):
        resposta.append(f"Considerando apenas operações de {filtros['categoria']}.")
    
    # Adicionar informação sobre porto
    if filtros.get('porto'):
        resposta.append(f"No porto de {filtros['porto']}.")
    
    # Adicionar detalhes adicionais se disponíveis
    if 'VOLUMES' in df.columns:
        total_volumes = df['VOLUMES'].sum()
        resposta.append(f"Total de volumes: {total_volumes:,.2f}")
    
    if 'VOLUME (M³)' in df.columns:
        total_volume_m3 = df['VOLUME (M³)'].sum()
        resposta.append(f"Volume total: {total_volume_m3:,.2f} m³")
    
    if 'PESO BRUTO' in df.columns:
        total_peso = df['PESO BRUTO'].sum()
        resposta.append(f"Peso bruto total: {total_peso:,.2f} kg")
    
    return " ".join(resposta)

def gerar_resposta_comparacao(df, filtros):
    """Gera resposta para perguntas de comparação"""
    # Preparar períodos para comparação
    if not (filtros.get('data_inicio') and filtros.get('data_fim')):
        return "Não foi possível identificar os períodos para comparação."
    
    data_inicio = pd.to_datetime(filtros['data_inicio'])
    data_fim = pd.to_datetime(filtros['data_fim'])
    
    # Separar dados por período
    df_periodo1 = df[df['ANO/MÊS'] == data_inicio]
    df_periodo2 = df[df['ANO/MÊS'] == data_fim]
    
    # Calcular totais
    total1 = unificar_contagem_containers(df_periodo1)
    total2 = unificar_contagem_containers(df_periodo2)
    
    # Calcular variação
    if total1 > 0:
        variacao_pct = ((total2 - total1) / total1) * 100
    else:
        variacao_pct = float('inf') if total2 > 0 else 0
    
    # Construir resposta
    resposta = []
    resposta.append(f"Comparação de containers movimentados:")
    resposta.append(f"- {data_inicio.strftime('%B/%Y')}: {total1:,} containers")
    resposta.append(f"- {data_fim.strftime('%B/%Y')}: {total2:,} containers")
    
    if variacao_pct != float('inf'):
        resposta.append(f"Variação: {variacao_pct:,.1f}%")
        if variacao_pct > 0:
            resposta.append("Houve um aumento no volume.")
        elif variacao_pct < 0:
            resposta.append("Houve uma redução no volume.")
        else:
            resposta.append("O volume se manteve estável.")
    
    # Adicionar detalhes por categoria se disponível
    if 'Categoria' in df.columns:
        for categoria in df['Categoria'].unique():
            df_cat1 = df_periodo1[df_periodo1['Categoria'] == categoria]
            df_cat2 = df_periodo2[df_periodo2['Categoria'] == categoria]
            total_cat1 = unificar_contagem_containers(df_cat1)
            total_cat2 = unificar_contagem_containers(df_cat2)
            if total_cat1 > 0 or total_cat2 > 0:
                resposta.append(f"\n{categoria}:")
                resposta.append(f"- {data_inicio.strftime('%B/%Y')}: {total_cat1:,}")
                resposta.append(f"- {data_fim.strftime('%B/%Y')}: {total_cat2:,}")
    
    return "\n".join(resposta)

def gerar_resposta_ranking(df, filtros, campo_ranking='ARMADOR', n_items=5):
    """Gera resposta para perguntas de ranking"""
    # Agrupar dados
    ranking = df.groupby(campo_ranking).apply(unificar_contagem_containers).sort_values(ascending=False)
    
    # Construir resposta
    resposta = []
    
    # Adicionar contexto
    if filtros.get('porto'):
        resposta.append(f"Top {n_items} {campo_ranking.lower()}es em {filtros.get('ano', 'período analisado')} no porto de {filtros['porto']}:")
    else:
        resposta.append(f"Top {n_items} {campo_ranking.lower()}es em {filtros.get('ano', 'período analisado')}:")
    
    # Adicionar ranking
    for i, (nome, total) in enumerate(ranking.head(n_items).items(), 1):
        resposta.append(f"{i}. {nome.lower()}: {int(total)} containers")
    
    # Adicionar informações adicionais
    total_geral = unificar_contagem_containers(df)
    total_top = ranking.head(n_items).sum()
    
    if total_geral > 0:
        pct_top = (total_top / total_geral) * 100
        resposta.append(f"\nOs top {n_items} representam {pct_top:.1f}% do total de {total_geral:,} containers.")
    
    return "\n".join(resposta)

def gerar_resposta_tendencia(df, filtros):
    """Gera resposta para análise de tendência"""
    # Agrupar por mês
    tendencia = df.groupby(['ano', 'mes']).apply(unificar_contagem_containers).reset_index()
    tendencia['data'] = pd.to_datetime(tendencia[['ano', 'mes']].assign(day=1))
    tendencia = tendencia.sort_values('data')
    
    # Pegar os últimos 3 meses
    ultimos_meses = tendencia.tail(3)
    
    # Calcular variações
    variacoes = []
    for i in range(1, len(ultimos_meses)):
        mes_anterior = ultimos_meses.iloc[i-1]
        mes_atual = ultimos_meses.iloc[i]
        if mes_anterior.iloc[-1] > 0:  # último valor é o total de containers
            var_pct = ((mes_atual.iloc[-1] - mes_anterior.iloc[-1]) / mes_anterior.iloc[-1]) * 100
            variacoes.append(var_pct)
    
    # Construir resposta
    resposta = ["Análise de tendência dos últimos 3 meses:"]
    
    for _, row in ultimos_meses.iterrows():
        data = row['data']
        total = row.iloc[-1]  # último valor é o total de containers
        resposta.append(f"- {data.strftime('%B/%Y')}: {int(total):,} containers")
    
    # Adicionar análise de variação
    if variacoes:
        var_media = sum(variacoes) / len(variacoes)
        if var_media > 5:
            resposta.append("\nTendência: CRESCIMENTO SIGNIFICATIVO")
        elif var_media > 0:
            resposta.append("\nTendência: CRESCIMENTO MODERADO")
        elif var_media < -5:
            resposta.append("\nTendência: QUEDA SIGNIFICATIVA")
        elif var_media < 0:
            resposta.append("\nTendência: QUEDA MODERADA")
        else:
            resposta.append("\nTendência: ESTÁVEL")
        
        resposta.append(f"Variação média: {var_media:.1f}%")
    
    return "\n".join(resposta)

def responder_pergunta(df, tipo_analise, filtros):
    """Gera uma resposta com base no tipo de análise e filtros"""
    if df.empty:
        return "Não foram encontrados dados para os filtros especificados."
    
    if tipo_analise == 'total':
        return gerar_resposta_total(df, filtros)
    elif tipo_analise == 'comparacao':
        return gerar_resposta_comparacao(df, filtros)
    elif tipo_analise == 'ranking':
        return gerar_resposta_ranking(df, filtros)
    elif tipo_analise == 'tendencia':
        return gerar_resposta_tendencia(df, filtros)
    else:
        return "Tipo de análise não suportado."

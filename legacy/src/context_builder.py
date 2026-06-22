"""
Módulo responsável pela construção do contexto para a API
"""
from .config import ANALISE_CONFIG

def construir_contexto(df, pergunta, filtros, detalhado=False):
    """Constrói o contexto para a API com base nos dados filtrados"""
    if df.empty:
        return "Não há dados disponíveis para análise."
    
    contexto = []
    
    # Informações básicas
    total_registros = len(df)
    contexto.append(f"Total de registros: {total_registros}")
    
    # Período dos dados
    if 'data_embarque_padronizada' in df.columns:
        data_min = df['data_embarque_padronizada'].min()
        data_max = df['data_embarque_padronizada'].max()
        contexto.append(f"Período dos dados: de {data_min.strftime('%d/%m/%Y')} até {data_max.strftime('%d/%m/%Y')}")
    elif 'ano' in df.columns and 'mes' in df.columns:
        anos = sorted(df['ano'].unique())
        meses = sorted(df['mes'].unique())
        contexto.append(f"Anos disponíveis: {anos}")
        contexto.append(f"Meses disponíveis: {meses}")
    
    # Métricas principais
    if 'qtd_container' in df.columns:
        total_containers = df['qtd_container'].sum()
        contexto.append(f"Total de containers: {total_containers:,.0f}")
    
    # Análise por porto
    for tipo in ['importacao', 'exportacao', 'cabotagem']:
        colunas_porto = [col for col in df.columns if 'PORTO' in col.upper()]
        if colunas_porto:
            for col in colunas_porto:
                portos_principais = df[col].value_counts().head(5)
                if not portos_principais.empty:
                    contexto.append(f"\nPrincipais {col}:")
                    for porto, qtd in portos_principais.items():
                        if porto and str(porto).strip():
                            contexto.append(f"- {porto}: {qtd:,.0f} registros")
    
    # Análise por cliente
    colunas_cliente = [col for col in df.columns if any(termo in col.upper() for termo in ['CLIENTE', 'CONSIGNATARIO', 'EXPORTADOR', 'IMPORTADOR'])]
    if colunas_cliente:
        for col in colunas_cliente:
            clientes_principais = df[col].value_counts().head(5)
            if not clientes_principais.empty:
                contexto.append(f"\nPrincipais {col}:")
                for cliente, qtd in clientes_principais.items():
                    if cliente and str(cliente).strip():
                        contexto.append(f"- {cliente}: {qtd:,.0f} registros")
    
    # Análise temporal
    if 'data_embarque_padronizada' in df.columns:
        df['ano_mes'] = df['data_embarque_padronizada'].dt.to_period('M')
        serie_temporal = df.groupby('ano_mes')['qtd_container'].sum()
        
        if not serie_temporal.empty:
            contexto.append("\nEvolução temporal (containers por mês):")
            for periodo, qtd in serie_temporal.tail(6).items():
                contexto.append(f"- {periodo}: {qtd:,.0f}")
            
            # Calcular variação
            if len(serie_temporal) >= 2:
                ultima = serie_temporal.iloc[-1]
                penultima = serie_temporal.iloc[-2]
                if penultima != 0:
                    variacao = ((ultima - penultima) / penultima) * 100
                    contexto.append(f"Variação em relação ao mês anterior: {variacao:.1f}%")
    
    # Análise detalhada (se solicitado)
    if detalhado:
        # Adicionar mais métricas
        for categoria, metricas in ANALISE_CONFIG['metricas_principais'].items():
            for metrica in metricas:
                if metrica in df.columns:
                    if df[metrica].dtype in ['int64', 'float64']:
                        total = df[metrica].sum()
                        media = df[metrica].mean()
                        contexto.append(f"\n{metrica}:")
                        contexto.append(f"- Total: {total:,.2f}")
                        contexto.append(f"- Média: {media:,.2f}")
        
        # Adicionar distribuição por dimensões relevantes
        for dimensao, colunas in ANALISE_CONFIG['dimensoes_analise'].items():
            for coluna in colunas:
                if coluna in df.columns:
                    distribuicao = df[coluna].value_counts()
                    if not distribuicao.empty:
                        contexto.append(f"\nDistribuição por {coluna}:")
                        for valor, contagem in distribuicao.head(10).items():
                            if valor and str(valor).strip():
                                contexto.append(f"- {valor}: {contagem:,.0f}")
    
    return "\n".join(contexto)

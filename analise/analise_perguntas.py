import pandas as pd
import re
import unicodedata
import os

# Função para normalizar texto: remove acentos e converte para minúsculas
def normalize_text(text):
    if isinstance(text, str):
        return unicodedata.normalize('NFKD', text).encode('ascii', errors='ignore').decode('utf-8').lower().strip()
    return text

# Carrega os dados
try:
    file_path = 'Dados_Consolidados.xlsx'
    df = pd.read_excel(file_path)
    
    # Exibe informações iniciais para debug
    print("Colunas disponíveis no DataFrame:")
    for col in df.columns:
        print(f"- {col}")
    print("\nPrimeiras linhas:")
    print(df.head(2).to_string())
    print("\nEstrutura dos dados:")
    print(df.info())
    
    # Normaliza nomes de colunas
    df.columns = [normalize_text(col) for col in df.columns]
    print("\nColunas após normalização:")
    for col in df.columns:
        print(f"- {col}")
    
    # Verificar se existem dados para 2025
    if 'data embarque' in df.columns:
        df['data embarque'] = pd.to_datetime(df['data embarque'], errors='coerce')
        df['ano'] = df['data embarque'].dt.year
        df['mes'] = df['data embarque'].dt.month
        print("\nAnos disponíveis nos dados:")
        print(df['ano'].unique())
    
    # Verifica se existe coluna relacionada a quantidade de containers
    colunas_container = [col for col in df.columns if 'container' in col or 'qtd' in col]
    print("\nColunas relacionadas a containers:")
    print(colunas_container)
    
    # Se encontrarmos a coluna de quantidade, vamos usá-la para as análises
    if colunas_container:
        qtd_col = colunas_container[0]  # Usa a primeira coluna encontrada
        print(f"\nUsando coluna '{qtd_col}' para contagem de containers")
        
        # Converte a coluna para numérico
        df[qtd_col] = pd.to_numeric(df[qtd_col], errors='coerce').fillna(0)
        
        # Análise das perguntas
        print("\n\nAnálise das perguntas:")
        
        # Pergunta 1
        print("\n1 - No ano de 2025, quantos containers foram movimentados pelo consignatário DC LOGISTICS BRASIL LTDA?")
        consignatario = "DC LOGISTICS BRASIL LTDA"
        
        # Identifica colunas de cliente
        colunas_cliente = [col for col in df.columns if 'consignatario' in col or 'exportador' in col or 'importador' in col]
        print(f"Colunas de cliente identificadas: {colunas_cliente}")
        
        # Filtrar para o ano 2025 e o consignatário específico
        filtro_ano = df['ano'] == 2025
        
        # Verificar em todas as colunas possíveis de cliente
        filtro_cliente = pd.Series(False, index=df.index)
        for col in colunas_cliente:
            filtro_cliente = filtro_cliente | df[col].str.contains(consignatario, case=False, na=False)
        
        resultado1 = df[filtro_ano & filtro_cliente][qtd_col].sum()
        print(f"Resposta: {resultado1:.0f} containers")
        
        # Pergunta 2
        print("\n2 - No ano de 2025, quantos containers foram movimentados pelo consignatário ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA?")
        consignatario = "ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA"
        
        # Filtrar para o cliente específico
        filtro_cliente = pd.Series(False, index=df.index)
        for col in colunas_cliente:
            filtro_cliente = filtro_cliente | df[col].str.contains(consignatario, case=False, na=False)
        
        resultado2 = df[filtro_ano & filtro_cliente][qtd_col].sum()
        print(f"Resposta: {resultado2:.0f} containers")
        
        # Pergunta 3
        print("\n3 - Quantos containers foram movimentados em março de 2025?")
        filtro_mes = (df['ano'] == 2025) & (df['mes'] == 3)
        resultado3 = df[filtro_mes][qtd_col].sum()
        print(f"Resposta: {resultado3:.0f} containers")
        
        # Pergunta 4
        print("\n4 - Na operação de importação, qual empresa mais trouxe containers para o porto do Rio de Janeiro em fevereiro de 2025 e qual foi o total?")
        filtro_operacao = df['tipo_operacao'] == 'importacao' if 'tipo_operacao' in df.columns else df['categoria'] == 'Importação'
        filtro_tempo = (df['ano'] == 2025) & (df['mes'] == 2)
        
        # Verificar diferentes colunas para encontrar porto Rio de Janeiro
        colunas_porto = [col for col in df.columns if 'porto' in col]
        filtro_porto = pd.Series(False, index=df.index)
        for col in colunas_porto:
            filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False)
        
        # Filtrar dados
        dados_filtrados = df[filtro_operacao & filtro_tempo & filtro_porto]
        
        # Agrupar por empresas (considerando várias colunas possíveis)
        resultado_empresas = {}
        for col in colunas_cliente:
            if col in df.columns:
                temp = dados_filtrados.groupby(col)[qtd_col].sum()
                for empresa, valor in temp.items():
                    if empresa and pd.notna(empresa) and valor > 0:
                        resultado_empresas[empresa] = resultado_empresas.get(empresa, 0) + valor
        
        if resultado_empresas:
            empresa_principal = max(resultado_empresas.items(), key=lambda x: x[1])
            print(f"Resposta: {empresa_principal[0]} com {empresa_principal[1]:.0f} containers")
        else:
            print("Resposta: Não foram encontrados dados correspondentes aos critérios.")
        
        # Pergunta 5
        print("\n5 - Na operação de exportação, quantos containers foram exportados a partir do porto de embarque do Rio de Janeiro?")
        filtro_operacao = df['tipo_operacao'] == 'exportacao' if 'tipo_operacao' in df.columns else df['categoria'] == 'Exportação'
        
        # Verificar porto de embarque Rio de Janeiro
        colunas_porto_embarque = [col for col in df.columns if 'porto' in col and 'embarque' in col or 'porto origem' in col]
        filtro_porto = pd.Series(False, index=df.index)
        for col in colunas_porto_embarque:
            filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False)
        
        resultado5 = df[filtro_operacao & filtro_porto][qtd_col].sum()
        print(f"Resposta: {resultado5:.0f} containers")
    else:
        print("\nNenhuma coluna de quantidade de containers encontrada.")

except Exception as e:
    import traceback
    print(f"Erro ao analisar os dados: {e}")
    print(traceback.format_exc())

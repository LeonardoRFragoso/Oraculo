import pandas as pd
import numpy as np
import sys

print("Iniciando análise de dados...")
print(f"Versão do pandas: {pd.__version__}")

# Carregar dados com menos inferência automática
try:
    xlsx_file = 'Dados_Consolidados.xlsx'
    print(f"Carregando {xlsx_file}...")
    
    # Carregar dados sem conversão automática de tipos
    df = pd.read_excel(xlsx_file, dtype=str)
    print(f"Carregado com sucesso. Total de registros: {len(df)}")
    
    # Explorar estrutura básica
    print("\nEstrutura dos dados:")
    print(f"Colunas: {len(df.columns)}")
    
    # Verificar colunas de quantidade de containers
    container_cols = [col for col in df.columns if 'CONTAINER' in str(col).upper()]
    print(f"\nColunas relacionadas a containers: {container_cols}")
    
    # Verificar coluna ANO/MÊS
    if 'ANO/MÊS' in df.columns:
        # Converter para numérico 
        df['ANO/MÊS'] = pd.to_numeric(df['ANO/MÊS'], errors='coerce')
        
        # Extrair ano e mês
        df['ANO'] = df['ANO/MÊS'].fillna(0).astype(int) // 100
        df['MES'] = df['ANO/MÊS'].fillna(0).astype(int) % 100
        
        # Verificar anos disponíveis
        anos = df['ANO'].unique()
        print(f"\nAnos disponíveis nos dados: {sorted(anos)}")
        
        # Verificar se 2025 está presente
        if 2025 in anos:
            contagem_2025 = (df['ANO'] == 2025).sum()
            print(f"Registros para 2025: {contagem_2025}")
        else:
            print("AVISO: Não há registros para o ano 2025!")
    else:
        print("\nAVISO: Coluna ANO/MÊS não encontrada!")
    
    # Determinar a coluna de quantidade de containers mais adequada
    qtd_col = None
    
    # Tentar identificar a coluna correta
    candidatos = []
    for col in container_cols:
        # Converter temporariamente para numérico e verificar se há valores
        temp_series = pd.to_numeric(df[col], errors='coerce')
        soma = temp_series.sum()
        if not pd.isna(soma) and soma > 0:
            candidatos.append((col, soma))
    
    if candidatos:
        # Ordenar por soma total (maior primeiro)
        candidatos.sort(key=lambda x: x[1], reverse=True)
        qtd_col = candidatos[0][0]
        print(f"\nColuna selecionada para quantidade de containers: {qtd_col} (soma={candidatos[0][1]})")
    else:
        # Verificar se há colunas C20, C40 que poderiam ser somadas
        if 'C20' in df.columns and 'C40' in df.columns:
            df['C20'] = pd.to_numeric(df['C20'], errors='coerce').fillna(0)
            df['C40'] = pd.to_numeric(df['C40'], errors='coerce').fillna(0)
            df['TOTAL_CONTAINERS'] = df['C20'] + df['C40']
            qtd_col = 'TOTAL_CONTAINERS'
            print(f"\nUsando soma de C20 + C40 como quantidade de containers: {qtd_col}")
        else:
            print("\nERRO: Não foi possível determinar a coluna de quantidade de containers!")
            sys.exit(1)
    
    # Converter a coluna escolhida para numérico
    df[qtd_col] = pd.to_numeric(df[qtd_col], errors='coerce').fillna(0)
    
    # Verificar colunas de cliente
    cliente_cols = [col for col in df.columns if any(x in str(col).upper() for x in ['CONSIGNATARIO', 'EXPORTADOR', 'IMPORTADOR'])]
    print(f"\nColunas relacionadas a clientes: {cliente_cols}")
    
    # Verificar categorias/operações
    if 'Categoria' in df.columns:
        print("\nTipos de operações:")
        valores_categoria = df['Categoria'].value_counts()
        print(valores_categoria)
        
        # Mapear categorias para operações
        df['OPERACAO'] = df['Categoria'].map({
            'Importação': 'importacao',
            'Exportação': 'exportacao',
            'Cabotagem': 'cabotagem'
        })
    
    # Verificar portos
    porto_cols = [col for col in df.columns if 'PORTO' in str(col).upper()]
    print(f"\nColunas relacionadas a portos: {porto_cols}")
    
    # Verificando se o ano 2023 está presente para fins de comparação
    if 'ANO' in df.columns and 2023 in df['ANO'].unique():
        print("\nVerificando dados de 2023 como exemplo:")
        count_2023 = (df['ANO'] == 2023).sum()
        sum_2023 = df.loc[df['ANO'] == 2023, qtd_col].sum()
        print(f"Registros em 2023: {count_2023}, Total de containers: {sum_2023:.0f}")
    
    # Agora responder às perguntas originais, adaptando para 2023 se 2025 não existir
    ano_analise = 2025 if 2025 in df['ANO'].unique() else 2023
    
    print(f"\n\nRespondendo às perguntas com dados de {ano_analise}:")
    
    # Pergunta 1
    print(f"\n1. No ano de {ano_analise}, quantos containers foram movimentados pelo consignatário DC LOGISTICS BRASIL LTDA?")
    cliente = "DC LOGISTICS BRASIL LTDA"
    
    filtro_ano = df['ANO'] == ano_analise
    filtro_cliente = pd.Series(False, index=df.index)
    
    for col in cliente_cols:
        filtro_cliente = filtro_cliente | df[col].str.contains(cliente, case=False, na=False, regex=False)
    
    resultado_dc = df.loc[filtro_ano & filtro_cliente, qtd_col].sum()
    print(f"Resposta: {resultado_dc:.0f} containers")
    
    # Pergunta 2
    print(f"\n2. No ano de {ano_analise}, quantos containers foram movimentados pelo consignatário ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA?")
    cliente = "ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA"
    
    filtro_cliente = pd.Series(False, index=df.index)
    for col in cliente_cols:
        # Usar regex=False para evitar erros com caracteres especiais
        filtro_cliente = filtro_cliente | df[col].str.contains(cliente, case=False, na=False, regex=False)
    
    resultado_accumed = df.loc[filtro_ano & filtro_cliente, qtd_col].sum()
    print(f"Resposta: {resultado_accumed:.0f} containers")
    
    # Pergunta 3
    print(f"\n3. Quantos containers foram movimentados em março de {ano_analise}?")
    filtro_mes = (df['ANO'] == ano_analise) & (df['MES'] == 3)
    resultado_marco = df.loc[filtro_mes, qtd_col].sum()
    print(f"Resposta: {resultado_marco:.0f} containers")
    
    # Pergunta 4
    print(f"\n4. Na operação de importação, qual empresa mais trouxe containers para o porto do Rio de Janeiro em fevereiro de {ano_analise}?")
    
    filtro_operacao = df['OPERACAO'] == 'importacao'
    filtro_tempo = (df['ANO'] == ano_analise) & (df['MES'] == 2)
    
    filtro_porto = pd.Series(False, index=df.index)
    for col in porto_cols:
        # Usar regex=False para evitar erros com caracteres especiais
        filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False, regex=False)
    
    dados_filtrados = df.loc[filtro_operacao & filtro_tempo & filtro_porto]
    
    top_empresas = {}
    for col in cliente_cols:
        # Agrupar por cliente e somar containers de forma segura
        if col in dados_filtrados.columns:
            temp = dados_filtrados.groupby(col)[qtd_col].sum()
            for empresa, valor in temp.items():
                if pd.notna(empresa) and str(empresa).strip() and valor > 0:
                    empresa_str = str(empresa).strip()
                    top_empresas[empresa_str] = top_empresas.get(empresa_str, 0) + valor
    
    if top_empresas:
        empresa_topo = max(top_empresas.items(), key=lambda x: x[1])
        print(f"Resposta: {empresa_topo[0]} com {empresa_topo[1]:.0f} containers")
    else:
        print(f"Não foram encontrados dados para importação no Rio de Janeiro em fevereiro de {ano_analise}")
    
    # Pergunta 5
    print(f"\n5. Na operação de exportação, quantos containers foram exportados a partir do porto de embarque do Rio de Janeiro?")
    
    filtro_operacao = df['OPERACAO'] == 'exportacao'
    
    embarque_cols = [col for col in porto_cols if any(x in str(col).upper() for x in ['EMBARQUE', 'ORIGEM'])]
    if not embarque_cols:
        embarque_cols = porto_cols
    
    filtro_porto = pd.Series(False, index=df.index)
    for col in embarque_cols:
        filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False, regex=False)
    
    resultado_exportacao = df.loc[filtro_operacao & filtro_porto, qtd_col].sum()
    print(f"Resposta: {resultado_exportacao:.0f} containers")

except Exception as e:
    import traceback
    print(f"ERRO: {e}")
    print(traceback.format_exc())

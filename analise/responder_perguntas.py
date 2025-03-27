import pandas as pd
import numpy as np
import re

# Carrega os dados consolidados
print("Carregando dados...")
df = pd.read_excel('Dados_Consolidados.xlsx')

# Preparação dos dados
print("Preparando dados...")

# Normaliza categorias
if 'Categoria' in df.columns:
    df['OPERACAO'] = df['Categoria'].apply(lambda x: 'importacao' if x == 'Importação' else 
                                          ('exportacao' if x == 'Exportação' else 'cabotagem'))

# Extrai ano e mês da coluna ANO/MÊS se disponível
if 'ANO/MÊS' in df.columns:
    df['ANO'] = df['ANO/MÊS'] // 100
    df['MES'] = df['ANO/MÊS'] % 100

# Converter colunas de containers para numérico
container_cols = []
for col in df.columns:
    if 'CONTAINER' in str(col).upper() or 'QTD' in str(col).upper():
        container_cols.append(col)

if 'QTD. CONTAINER' in df.columns:
    df['QTD. CONTAINER'] = pd.to_numeric(df['QTD. CONTAINER'], errors='coerce').fillna(0)
    qtd_col = 'QTD. CONTAINER'
elif container_cols:
    qtd_col = container_cols[0]
    df[qtd_col] = pd.to_numeric(df[qtd_col], errors='coerce').fillna(0)
else:
    # Usar a soma de C20 e C40 como alternativa
    if 'C20' in df.columns and 'C40' in df.columns:
        df['C20'] = pd.to_numeric(df['C20'], errors='coerce').fillna(0)
        df['C40'] = pd.to_numeric(df['C40'], errors='coerce').fillna(0)
        df['QTD_CONTAINERS'] = df['C20'] + df['C40']
        qtd_col = 'QTD_CONTAINERS'

print(f"Usando coluna '{qtd_col}' para contagem de containers")

# 1. No ano de 2025, quantos containers foram movimentados pelo consignatário DC LOGISTICS BRASIL LTDA?
print("\n1. No ano de 2025, quantos containers foram movimentados pelo consignatário DC LOGISTICS BRASIL LTDA?")
cliente = "DC LOGISTICS BRASIL LTDA"

# Identificar todas as colunas que podem conter informações de cliente
cliente_cols = [col for col in df.columns if 'CONSIGNATARIO' in str(col).upper() or 'EXPORTADOR' in str(col).upper() or 'IMPORTADOR' in str(col).upper()]

# Filtrar por ano 2025 e cliente DC LOGISTICS
filtro_ano = df['ANO'] == 2025
filtro_cliente = pd.Series(False, index=df.index)

for col in cliente_cols:
    try:
        df[col] = df[col].astype(str)
        filtro_cliente = filtro_cliente | df[col].str.contains(cliente, case=False, na=False)
    except:
        pass

resultado_dc = df[filtro_ano & filtro_cliente][qtd_col].sum()
print(f"Resposta: {resultado_dc:.0f} containers")

# 2. No ano de 2025, quantos containers foram movimentados pelo consignatário ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA?
print("\n2. No ano de 2025, quantos containers foram movimentados pelo consignatário ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA?")
cliente = "ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA"

filtro_cliente = pd.Series(False, index=df.index)
for col in cliente_cols:
    try:
        filtro_cliente = filtro_cliente | df[col].str.contains(cliente, case=False, na=False)
    except:
        pass

resultado_accumed = df[filtro_ano & filtro_cliente][qtd_col].sum()
print(f"Resposta: {resultado_accumed:.0f} containers")

# 3. Quantos containers foram movimentados em março de 2025?
print("\n3. Quantos containers foram movimentados em março de 2025?")
filtro_mes = (df['ANO'] == 2025) & (df['MES'] == 3)
resultado_marco = df[filtro_mes][qtd_col].sum()
print(f"Resposta: {resultado_marco:.0f} containers")

# 4. Na operação de importação, qual empresa mais trouxe containers para o porto do Rio de Janeiro em fevereiro de 2025 e qual foi o total?
print("\n4. Na operação de importação, qual empresa mais trouxe containers para o porto do Rio de Janeiro em fevereiro de 2025 e qual foi o total?")

# Filtros
filtro_operacao = df['OPERACAO'] == 'importacao'
filtro_tempo = (df['ANO'] == 2025) & (df['MES'] == 2)

# Verificar colunas de porto
porto_cols = [col for col in df.columns if 'PORTO' in str(col).upper()]
filtro_porto = pd.Series(False, index=df.index)

for col in porto_cols:
    try:
        df[col] = df[col].astype(str)
        filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False)
    except:
        pass

dados_filtrados = df[filtro_operacao & filtro_tempo & filtro_porto]

# Encontrar empresa com maior movimentação
top_empresas = {}
for col in cliente_cols:
    try:
        # Agrupar por cliente e somar containers
        temp = dados_filtrados.groupby(col)[qtd_col].sum()
        # Adicionar resultados ao dicionário
        for empresa, valor in temp.items():
            if pd.notna(empresa) and str(empresa).strip() and valor > 0:
                empresa_str = str(empresa).strip()
                top_empresas[empresa_str] = top_empresas.get(empresa_str, 0) + valor
    except Exception as e:
        print(f"Erro na coluna {col}: {e}")

if top_empresas:
    # Encontrar a empresa com maior valor
    empresa_topo = max(top_empresas.items(), key=lambda x: x[1])
    print(f"Resposta: {empresa_topo[0]} com {empresa_topo[1]:.0f} containers")
else:
    print("Resposta: Não foram encontrados dados correspondentes aos critérios.")

# 5. Na operação de exportação, quantos containers foram exportados a partir do porto de embarque do Rio de Janeiro?
print("\n5. Na operação de exportação, quantos containers foram exportados a partir do porto de embarque do Rio de Janeiro?")
filtro_operacao = df['OPERACAO'] == 'exportacao'

# Verificar colunas específicas de porto de embarque
embarque_cols = [col for col in porto_cols if 'EMBARQUE' in str(col).upper() or 'ORIGEM' in str(col).upper()]
if not embarque_cols:
    embarque_cols = porto_cols  # Usar todas as colunas de porto se não encontrar específicas

filtro_porto = pd.Series(False, index=df.index)
for col in embarque_cols:
    try:
        filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False)
    except:
        pass

resultado_exportacao = df[filtro_operacao & filtro_porto][qtd_col].sum()
print(f"Resposta: {resultado_exportacao:.0f} containers")

import pandas as pd
import sys

def analisar_dados():
    try:
        print("Carregando dados...")
        df = pd.read_excel('Dados_Consolidados.xlsx', dtype=str)
        print(f"Dados carregados: {len(df)} registros")
        
        # Criar colunas de ano e mês
        df['ANO/MÊS'] = pd.to_numeric(df['ANO/MÊS'], errors='coerce')
        df['ANO'] = df['ANO/MÊS'].fillna(0).astype(int) // 100
        df['MES'] = df['ANO/MÊS'].fillna(0).astype(int) % 100
        
        # Criar coluna de total de containers
        df['C20'] = pd.to_numeric(df['C20'], errors='coerce').fillna(0)
        df['C40'] = pd.to_numeric(df['C40'], errors='coerce').fillna(0)
        df['TOTAL_CONTAINERS'] = df['C20'] + df['C40']
        
        # Mapear categorias
        df['OPERACAO'] = df['Categoria'].map({
            'Importação': 'importacao',
            'Exportação': 'exportacao',
            'Cabotagem': 'cabotagem'
        })
        
        # Identificar colunas de cliente e porto
        cliente_cols = [col for col in df.columns if any(termo in str(col).upper() 
                      for termo in ['CONSIGNATARIO', 'IMPORTADOR', 'EXPORTADOR'])]
        
        porto_cols = [col for col in df.columns if 'PORTO' in str(col).upper()]
        
        # Resposta 1
        resposta1 = responder_pergunta1(df, cliente_cols)
        
        # Resposta 2
        resposta2 = responder_pergunta2(df, cliente_cols)
        
        # Resposta 3
        resposta3 = responder_pergunta3(df)
        
        # Resposta 4
        resposta4 = responder_pergunta4(df, cliente_cols, porto_cols)
        
        # Resposta 5
        resposta5 = responder_pergunta5(df, porto_cols)
        
        # Imprimir todas as respostas de forma organizada
        print("\n========== RESPOSTAS ÀS PERGUNTAS ==========\n")
        print("1. No ano de 2025, quantos containers foram movimentados pelo consignatário DC LOGISTICS BRASIL LTDA?")
        print(f"Resposta: {resposta1}\n")
        
        print("2. No ano de 2025, quantos containers foram movimentados pelo consignatário ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA?")
        print(f"Resposta: {resposta2}\n")
        
        print("3. Quantos containers foram movimentados em março de 2025?")
        print(f"Resposta: {resposta3}\n")
        
        print("4. Na operação de importação, qual empresa mais trouxe containers para o porto do Rio de Janeiro em fevereiro de 2025 e qual foi o total?")
        print(f"Resposta: {resposta4}\n")
        
        print("5. Na operação de exportação, quantos containers foram exportados a partir do porto de embarque do Rio de Janeiro?")
        print(f"Resposta: {resposta5}")
        
    except Exception as e:
        import traceback
        print(f"Erro: {e}")
        print(traceback.format_exc())

def responder_pergunta1(df, cliente_cols):
    cliente = "DC LOGISTICS BRASIL LTDA"
    filtro_ano = df['ANO'] == 2025
    
    filtro_cliente = pd.Series(False, index=df.index)
    for col in cliente_cols:
        filtro_cliente = filtro_cliente | df[col].str.contains(cliente, case=False, na=False, regex=False)
    
    total = df.loc[filtro_ano & filtro_cliente, 'TOTAL_CONTAINERS'].sum()
    return f"{total:.0f} containers"

def responder_pergunta2(df, cliente_cols):
    cliente = "ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA"
    filtro_ano = df['ANO'] == 2025
    
    filtro_cliente = pd.Series(False, index=df.index)
    for col in cliente_cols:
        filtro_cliente = filtro_cliente | df[col].str.contains(cliente, case=False, na=False, regex=False)
    
    total = df.loc[filtro_ano & filtro_cliente, 'TOTAL_CONTAINERS'].sum()
    return f"{total:.0f} containers"

def responder_pergunta3(df):
    filtro_mes = (df['ANO'] == 2025) & (df['MES'] == 3)
    total = df.loc[filtro_mes, 'TOTAL_CONTAINERS'].sum()
    return f"{total:.0f} containers"

def responder_pergunta4(df, cliente_cols, porto_cols):
    filtro_operacao = df['OPERACAO'] == 'importacao'
    filtro_tempo = (df['ANO'] == 2025) & (df['MES'] == 2)
    
    filtro_porto = pd.Series(False, index=df.index)
    for col in porto_cols:
        filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False, regex=False)
    
    dados_filtrados = df.loc[filtro_operacao & filtro_tempo & filtro_porto]
    
    if len(dados_filtrados) > 0:
        top_empresas = {}
        for col in cliente_cols:
            temp = dados_filtrados.groupby(col)['TOTAL_CONTAINERS'].sum()
            for empresa, valor in temp.items():
                if pd.notna(empresa) and str(empresa).strip() and valor > 0:
                    empresa_str = str(empresa).strip()
                    top_empresas[empresa_str] = top_empresas.get(empresa_str, 0) + valor
        
        if top_empresas:
            empresa_topo = max(top_empresas.items(), key=lambda x: x[1])
            return f"{empresa_topo[0]} com {empresa_topo[1]:.0f} containers"
        else:
            return "Não foram encontradas empresas que correspondam aos critérios."
    else:
        return "Não foram encontrados dados de importação para o porto do Rio de Janeiro em fevereiro de 2025."

def responder_pergunta5(df, porto_cols):
    filtro_operacao = df['OPERACAO'] == 'exportacao'
    
    embarque_cols = [col for col in porto_cols if any(x in str(col).upper() for x in ['EMBARQUE', 'ORIGEM'])]
    if not embarque_cols:
        embarque_cols = porto_cols
    
    filtro_porto = pd.Series(False, index=df.index)
    for col in embarque_cols:
        filtro_porto = filtro_porto | df[col].str.contains("RIO DE JANEIRO", case=False, na=False, regex=False)
    
    total = df.loc[filtro_operacao & filtro_porto, 'TOTAL_CONTAINERS'].sum()
    return f"{total:.0f} containers"

if __name__ == "__main__":
    analisar_dados()

import pandas as pd
import traceback

try:
    # Carrega os dados
    file_path = 'Dados_Consolidados.xlsx'
    print(f"Carregando dados de {file_path}...")
    df = pd.read_excel(file_path)
    
    # Informações básicas
    print(f"\nTotal de registros: {len(df)}")
    print(f"Total de colunas: {len(df.columns)}")
    
    # Lista as primeiras 30 colunas (para não sobrecarregar a saída)
    print("\nPrimeiras 30 colunas:")
    for i, col in enumerate(df.columns[:30]):
        print(f"{i+1}. {col}")
    
    # Verifica se há colunas relacionadas a contêineres
    container_cols = [col for col in df.columns if 'container' in str(col).lower() or 'cont' in str(col).lower()]
    print(f"\nColunas relacionadas a contêineres: {container_cols}")
    
    # Verifica se há colunas de datas
    date_cols = [col for col in df.columns if 'data' in str(col).lower() or 'date' in str(col).lower()]
    print(f"\nColunas de datas: {date_cols}")
    
    # Se encontrou coluna de data, verifica anos disponíveis
    if date_cols:
        print("\nExaminando dados temporais...")
        primeira_data = date_cols[0]
        df[primeira_data] = pd.to_datetime(df[primeira_data], errors='coerce')
        anos = df[primeira_data].dt.year.unique()
        print(f"Anos presentes nos dados: {sorted(anos[~pd.isna(anos)])}")
    
    # Lista valores únicos de categoria/operação
    if 'Categoria' in df.columns:
        print("\nTipos de operações:")
        print(df['Categoria'].value_counts())
    
    # Examina colunas relacionadas a clientes
    cliente_cols = [col for col in df.columns if 'consigna' in str(col).lower() or 'exportador' in str(col).lower() or 'importador' in str(col).lower()]
    print(f"\nColunas relacionadas a clientes: {cliente_cols}")
    
    # Verifica portos
    porto_cols = [col for col in df.columns if 'porto' in str(col).lower()]
    print(f"\nColunas relacionadas a portos: {porto_cols}")
    
    # Estrutura de dados
    print("\nTipos de dados nas colunas principais:")
    print(df.dtypes.head(10))

except Exception as e:
    print(f"Erro ao inspecionar dados: {e}")
    print(traceback.format_exc())

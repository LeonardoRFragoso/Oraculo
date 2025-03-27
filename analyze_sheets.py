import pandas as pd

# Analisar planilha consolidada
print("\nAnalisando planilha consolidada:")
print("-" * 80)
df_new = pd.read_excel('dados/Dados_Consolidados.xlsx')
print("\nPrimeiras 5 linhas:")
print(df_new.head())
print("\nColunas:")
for i, col in enumerate(df_new.columns, 1):
    print(f"{i}. {col}")

"""
Script de teste para validar as melhorias no sistema de respostas do GPTracker
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.advanced_llm import AdvancedLLMManager
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def create_sample_data():
    """Cria dados de exemplo para teste"""
    np.random.seed(42)
    
    # Dados simulados de containers
    clientes = [
        'ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA',
        'EMPRESA BRASILEIRA DE IMPORTACAO LTDA',
        'COMERCIAL SANTOS EXPORTADORA SA',
        'LOGISTICA INTERNACIONAL BRASIL LTDA',
        'TRADING COMPANY DO BRASIL LTDA',
        'IMPORTADORA SAO PAULO LTDA',
        'EXPORTADORA RIO DE JANEIRO SA',
        'COMERCIO EXTERIOR BRASIL LTDA'
    ]
    
    portos = ['SANTOS', 'RIO DE JANEIRO', 'PARANAGUA', 'ITAJAI', 'SUAPE']
    armadores = ['MAERSK', 'MSC', 'CMA CGM', 'HAPAG LLOYD', 'COSCO']
    
    # Gerar dados para 2024 e 2025
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(1000):
        # Data aleatória entre jan/2024 e mar/2025
        days_offset = np.random.randint(0, 450)
        data_embarque = base_date + timedelta(days=days_offset)
        
        record = {
            'consignatario': np.random.choice(clientes),
            'qtd_container': np.random.randint(1, 50),
            'teus': np.random.randint(1, 100),
            'porto': np.random.choice(portos),
            'armador': np.random.choice(armadores),
            'data_embarque': data_embarque.strftime('%Y-%m-%d'),
            'ano_mes': data_embarque.strftime('%Y-%m'),
            'mes': data_embarque.month,
            'ano': data_embarque.year
        }
        data.append(record)
    
    return pd.DataFrame(data)

def test_specific_queries(llm_manager, df):
    """Testa perguntas específicas das perguntas.txt"""
    
    test_queries = [
        "Quantos containers foram movimentados pelo consignatário ACCUMED PRODUTOS MEDICO HOSPITALARES LTDA em 2024?",
        "Qual foi o volume total de importações em março de 2025, considerando todos os portos?",
        "Quais são os principais armadores que operaram no porto de Santos em 2024, ordenados por quantidade de containers?",
        "Compare o volume de exportações entre janeiro e fevereiro de 2025",
        "Mostre uma análise de tendência do volume de containers movimentados nos últimos 3 meses",
        "Quais são os 10 maiores clientes por volume de containers?"
    ]
    
    print("=" * 80)
    print("TESTE DAS RESPOSTAS MELHORADAS DO GPTRACKER")
    print("=" * 80)
    print(f"Dados de teste: {len(df)} registros")
    print(f"Período: {df['data_embarque'].min()} a {df['data_embarque'].max()}")
    print(f"Clientes únicos: {df['consignatario'].nunique()}")
    print(f"Total de containers: {df['qtd_container'].sum():,}")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. PERGUNTA: {query}")
        print("-" * 60)
        
        try:
            response = llm_manager.generate_enhanced_response(query, df, max_tokens=800)
            print("RESPOSTA:")
            print(response)
            print("-" * 60)
            
        except Exception as e:
            print(f"ERRO: {str(e)}")
            print("-" * 60)

def test_data_analysis_methods(llm_manager, df):
    """Testa métodos específicos de análise"""
    print("\n" + "=" * 80)
    print("TESTE DOS MÉTODOS DE ANÁLISE ESPECÍFICA")
    print("=" * 80)
    
    test_cases = [
        "accumed produtos medicos",
        "março 2025 volume total",
        "santos armadores ranking",
        "janeiro fevereiro comparação",
        "tendência últimos meses"
    ]
    
    for query in test_cases:
        print(f"\nTeste: {query}")
        print("-" * 40)
        result = llm_manager._analyze_specific_query(query, df)
        print(result)
        print("-" * 40)

def main():
    """Função principal de teste"""
    print("Iniciando teste das melhorias do GPTracker...")
    
    # Verificar se a chave da OpenAI está configurada
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ ATENÇÃO: Chave da OpenAI não configurada!")
        print("Configure OPENAI_API_KEY no arquivo .env para testar as respostas completas.")
        print("Testando apenas os métodos de análise de dados...\n")
        test_only_analysis = True
    else:
        test_only_analysis = False
    
    # Criar dados de teste
    print("Criando dados de teste...")
    df = create_sample_data()
    
    # Inicializar LLM Manager
    llm_manager = AdvancedLLMManager()
    
    # Criar base de conhecimento com os dados de teste
    print("Criando base de conhecimento...")
    llm_manager.create_knowledge_base_from_data(df)
    
    # Testar métodos de análise específica
    test_data_analysis_methods(llm_manager, df)
    
    # Testar respostas completas se a chave estiver configurada
    if not test_only_analysis:
        test_specific_queries(llm_manager, df)
    else:
        print("\n" + "=" * 80)
        print("RESUMO DOS DADOS PARA TESTE MANUAL")
        print("=" * 80)
        print("Use estes dados para testar manualmente no GPTracker:")
        print(f"- Total de registros: {len(df)}")
        print(f"- ACCUMED containers: {df[df['consignatario'].str.contains('ACCUMED', na=False)]['qtd_container'].sum()}")
        print(f"- Santos containers: {df[df['porto'] == 'SANTOS']['qtd_container'].sum()}")
        print(f"- Top cliente: {df.groupby('consignatario')['qtd_container'].sum().idxmax()}")
        print(f"- Top armador Santos: {df[df['porto'] == 'SANTOS'].groupby('armador')['qtd_container'].sum().idxmax()}")
        
        # Salvar dados de teste
        test_file = "dados/processed/test_data_improved.xlsx"
        os.makedirs("dados/processed", exist_ok=True)
        df.to_excel(test_file, index=False)
        print(f"\nDados salvos em: {test_file}")
        print("Carregue este arquivo no GPTracker para testar as melhorias!")

if __name__ == "__main__":
    main()

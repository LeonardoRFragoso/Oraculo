#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para análise de dados logísticos e geração de insights utilizando um LLM open-source.
Requisitos:
- Python 3
- transformers
- langchain (com dependências community: pip install langchain[community])
- langchain-community (pip install -U langchain-community)
- pandas
- openpyxl
- torch
- accelerate

Para instalar todas as dependências necessárias, execute:
pip install transformers langchain[community] langchain-community pandas openpyxl torch accelerate
"""

import pandas as pd
from langchain_core.prompts import PromptTemplate  # Import atualizado para evitar warning
from langchain.chains import LLMChain             # Import atualizado para evitar warning
from langchain_community.llms import HuggingFacePipeline  # Import atualizado conforme aviso
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

def main():
    # Etapa 1: Carregar os dados das planilhas (certifique-se de que os arquivos estão no mesmo diretório)
    try:
        df_import = pd.read_excel('importação.xlsx')
        df_export = pd.read_excel('exportação.xlsx')
        df_cabotagem = pd.read_excel('cabotagem.xlsx')
    except Exception as e:
        print("Erro ao carregar as planilhas:", e)
        return

    # Etapa 2: Concatenar os dados em um único DataFrame e exibir as primeiras linhas
    dados_gerais = pd.concat([df_import, df_export, df_cabotagem], ignore_index=True)
    print("Planilhas carregadas e dados concatenados com sucesso.")
    print("Visualizando as primeiras linhas dos dados:")
    print(dados_gerais.head())

    # Limitar os dados enviados ao LLM para evitar sobrecarga
    dados_logisticos = dados_gerais.head(50).to_string()

    # Etapa 3: Carregar as informações dos clientes a partir do arquivo clientes.txt
    try:
        with open("clientes.txt", "r", encoding="utf-8") as f:
            dados_clientes = f.read()
    except Exception as e:
        print("Erro ao carregar o arquivo clientes.txt:", e)
        dados_clientes = "Nenhuma informação disponível."

    # Etapa 4: Configurar o modelo LLM via Hugging Face
    # Utilizando o modelo "tiiuae/falcon-7b-instruct" que é público e não requer autenticação.
    model_name = "tiiuae/falcon-7b-instruct"
    print(f"\nCarregando o modelo: {model_name}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,  # Utilize torch.float16 para maior compatibilidade com a maioria das GPUs
        device_map="auto"
    )

    generation_pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        temperature=0.7,
    )

    llm = HuggingFacePipeline(pipeline=generation_pipe)

    # Etapa 5: Criar o prompt para gerar insights, combinando dados logísticos e informações dos clientes
    prompt_template = (
        "Você é um analista especialista em logística portuária, comércio exterior e gestão de clientes.\n"
        "Analise os dados logísticos e as informações dos clientes abaixo e sugira insights detalhados sobre:\n"
        "- Estratégias para captar novos clientes;\n"
        "- Como aumentar a quantidade de contêineres alocados pelos clientes atuais em relação ao total movimentado;\n"
        "- Estratégias para melhorar o atendimento e otimizar a operação logística.\n\n"
        "Dados Logísticos:\n{dados_logisticos}\n\n"
        "Informações dos Clientes:\n{dados_clientes}\n\n"
        "Insights:"
    )
    prompt = PromptTemplate(template=prompt_template, input_variables=["dados_logisticos", "dados_clientes"])

    chain = LLMChain(prompt=prompt, llm=llm)

    # Etapa 6: Gerar e exibir os insights
    print("\nGerando insights com base nos dados e informações dos clientes...")
    resultado = chain.run({"dados_logisticos": dados_logisticos, "dados_clientes": dados_clientes})

    print("\n--- Insights Gerados ---\n")
    print(resultado)

if __name__ == '__main__':
    main()

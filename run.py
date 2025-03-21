import os
# Desabilita o file watcher do Streamlit para evitar conflitos com o PyTorch
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

import streamlit as st
import pandas as pd
import torch

# Ajusta o atributo __path__ de torch.classes para evitar o erro no file watcher
try:
    class DummyPath:
        _path = []
    setattr(torch.classes, '__path__', DummyPath())
except Exception as e:
    st.warning("Não foi possível ajustar torch.classes.__path__: " + str(e))

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import HuggingFacePipeline
import datetime

# Função para carregar as planilhas (apenas as 20 primeiras linhas de cada)
def carregar_planilhas():
    try:
        df_import = pd.read_excel('importação.xlsx', nrows=20)
        df_export = pd.read_excel('exportação.xlsx', nrows=20)
        df_cabotagem = pd.read_excel('cabotagem.xlsx', nrows=20)
        df = pd.concat([df_import, df_export, df_cabotagem], ignore_index=True)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar as planilhas: {e}")
        return pd.DataFrame()

# Função para carregar dados dos clientes
def carregar_clientes():
    try:
        with open("clientes.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.warning(f"Erro ao carregar clientes.txt: {e}")
        return ""

# Função para carregar o modelo LLM (usar cache para evitar recarregamento)
@st.cache_resource
def carregar_llm():
    model_name = "tiiuae/falcon-7b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,  # utilizando float32 para CPU
        device_map="cpu"             # força o carregamento do modelo na CPU
    )
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        temperature=0.7
    )
    return HuggingFacePipeline(pipeline=pipe)

# Função para gerar os insights
def gerar_insights(dados_logisticos, dados_clientes, llm):
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
    resultado = chain.run({"dados_logisticos": dados_logisticos, "dados_clientes": dados_clientes})
    return resultado

# Configurações da página
st.set_page_config(page_title="Oráculo Comercial Autônomo", layout="wide")
st.title("🤖 Oráculo Comercial Autônomo")
st.markdown("Este oráculo analisa diariamente os dados logísticos e de clientes para sugerir estratégias comerciais.")

# Informar que os dados estão sendo carregados e os insights gerados
st.info("Carregando dados e gerando insights...")

# Carrega dados e gera insights automaticamente ao iniciar o app
df = carregar_planilhas()
dados_clientes = carregar_clientes()
llm = carregar_llm()

if not df.empty:
    resumo_dados = df.head(50).to_string()
    insights = gerar_insights(resumo_dados, dados_clientes, llm)

    # Exibe os insights gerados
    st.subheader("💡 Insights do Dia")
    st.write(insights)

    # Exibe os dados lidos (opcional)
    with st.expander("Ver dados analisados"):
        st.dataframe(df.head(50))

    # Salva log do dia
    hoje = datetime.date.today().isoformat()
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/insights_{hoje}.txt", "w", encoding="utf-8") as f:
        f.write(insights)

    st.success(f"Insights salvos em logs/insights_{hoje}.txt")
else:
    st.error("Nenhum dado encontrado nas planilhas.")

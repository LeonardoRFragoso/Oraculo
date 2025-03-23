import streamlit as st
import pandas as pd
import openai

# Configure sua chave da API da OpenAI
openai.api_key = "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"

@st.cache_data
def load_data():
    # Altere o caminho conforme necessário
    df = pd.read_excel(r"C:\Users\leona\OneDrive\Documentos\Oraculo-Comercial\Dados_Consolidados.xlsx")
    
    # Converte colunas do tipo object para string, se necessário
    for col in df.select_dtypes(include=['object']).columns:
        if not df[col].map(lambda x: isinstance(x, str)).all():
            df[col] = df[col].astype(str)
    
    # Tenta converter a coluna "ANO/MÊS" para datetime e salva em uma nova coluna
    try:
        df["ANO/MÊS_parsed"] = pd.to_datetime(df["ANO/MÊS"], errors="coerce")
    except Exception as e:
        st.error(f"Erro ao converter 'ANO/MÊS' para datetime: {e}")
        df["ANO/MÊS_parsed"] = pd.NaT

    return df

df = load_data()

st.title("Oráculo Comercial")
st.write("Visualização dos dados comerciais:")
st.dataframe(df)

# Seção de depuração para visualizar os valores únicos das colunas de interesse
with st.expander("Depurar valores das colunas"):
    st.write("Valores únicos em PORTO DE DESCARGA:", df["PORTO DE DESCARGA"].unique())
    st.write("Valores únicos em ANO/MÊS:", df["ANO/MÊS"].unique())
    st.write("Valores únicos em ANO/MÊS_parsed (convertidos):", df["ANO/MÊS_parsed"].dropna().unique())

st.write("Faça sua pergunta sobre os dados:")
user_question = st.text_input("Pergunta:")

if st.button("Responder"):
    if user_question:
        question_lower = user_question.lower()
        # Se a pergunta for sobre containers no porto do Rio de Janeiro em fevereiro de 2025,
        # tentamos filtrar os dados diretamente.
        if ("rio de janeiro" in question_lower and "fevereiro" in question_lower and "2025" in question_lower 
            and "container" in question_lower):
            try:
                # Filtro para o porto
                filtro_porto = df["PORTO DE DESCARGA"].str.lower().str.contains("rio de janeiro", na=False)
                
                # Tenta filtrar usando a coluna convertida para datetime, se houver registros válidos
                if df["ANO/MÊS_parsed"].notna().any():
                    filtro_data = (df["ANO/MÊS_parsed"].dt.year == 2025) & (df["ANO/MÊS_parsed"].dt.month == 2)
                else:
                    # Se a conversão para datetime não foi possível, tenta um filtro alternativo por string
                    filtro_data = (df["ANO/MÊS"].str.contains("2025-02", na=False)) | (df["ANO/MÊS"].str.contains("2025/02", na=False))
                
                filtered_df = df[filtro_porto & filtro_data]
                
                st.write("Registros encontrados:", filtered_df.shape[0])
                
                if filtered_df.empty:
                    st.warning("Nenhum dado encontrado para o filtro especificado. Verifique os valores e formatos nas colunas.")
                else:
                    # Agrupa por empresa e soma a quantidade de containers
                    resultado = filtered_df.groupby("NOME IMPORTADOR")["QTDE CONTAINER"].sum().reset_index()
                    resultado = resultado.sort_values(by="QTDE CONTAINER", ascending=False)
                    top_empresa = resultado.iloc[0]
                    st.subheader("Resposta:")
                    st.write(
                        f"A empresa que mais trouxe containers para o porto do Rio de Janeiro em fevereiro de 2025 foi **{top_empresa['NOME IMPORTADOR']}**, com um total de **{top_empresa['QTDE CONTAINER']}** containers."
                    )
            except Exception as e:
                st.error(f"Erro ao processar os dados: {e}")
        else:
            # Para outras perguntas, utiliza a API da OpenAI (GPT-4)
            colunas = df.columns.tolist()
            prompt = (
                f"Você é um especialista em análise de dados comerciais. "
                f"Considere os dados com as seguintes colunas: {', '.join(colunas)}. "
                f"Responda à seguinte pergunta sobre esses dados: {user_question}"
            )
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Você é um assistente de análise de dados comerciais."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )
                answer = response['choices'][0]['message']['content']
                st.subheader("Resposta:")
                st.write(answer)
            except Exception as e:
                st.error(f"Erro ao processar a solicitação: {e}")
    else:
        st.warning("Por favor, insira uma pergunta.")

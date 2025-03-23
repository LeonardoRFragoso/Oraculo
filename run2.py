import os
import streamlit as st
import pandas as pd
import datetime
import openai

# Configure sua chave de API do OpenAI diretamente aqui
openai.api_key = "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"

def padronizar_planilha(df, tipo_operacao):
    """
    Padroniza o DataFrame de acordo com o tipo de operação (importação, exportação, cabotagem).
    Retorna um DataFrame com as colunas: ["cliente", "porto_descarga", "ano_mes", "qtd_container", "tipo_operacao"].
    Realiza conversões necessárias (ex.: converte quantidades para numérico, trata vírgulas, etc.).
    """
    df = df.copy()
    # Criar novas colunas conforme o tipo de operação:
    if tipo_operacao == "importacao":
        # Para importação, use:
        # - Cliente: "CONSIGNATÁRIO"
        # - Porto de descarga: "PORTO DESCARGA"
        # - Quantidade: "QTDE CONTAINER"
        df["cliente"] = df["CONSIGNATÁRIO"]
        df["porto_descarga"] = df["PORTO DESCARGA"]
        qtd_col = "QTDE CONTAINER"
    elif tipo_operacao == "exportacao":
        # Para exportação, use:
        # - Cliente: "NOME EXPORTADOR" (ou se não existir, tente "CONSIGNATÁRIO")
        if "NOME EXPORTADOR" in df.columns:
            df["cliente"] = df["NOME EXPORTADOR"]
        else:
            df["cliente"] = df["CONSIGNATÁRIO"]
        # Porto: Tente usar "PORTO DESCARGA" se existir, senão "PORTO DESTINO"
        if "PORTO DESCARGA" in df.columns:
            df["porto_descarga"] = df["PORTO DESCARGA"]
        else:
            df["porto_descarga"] = df["PORTO DESTINO"]
        qtd_col = "QTDE CONTEINER"  # Atenção à grafia
    elif tipo_operacao == "cabotagem":
        # Para cabotagem, use:
        # - Cliente: "DESTINATÁRIO"
        df["cliente"] = df["DESTINATÁRIO"]
        # Porto: Tente usar "PORTO DE DESCARGA" ou "PORTO DE DESTINO"
        if "PORTO DE DESCARGA" in df.columns:
            df["porto_descarga"] = df["PORTO DE DESCARGA"]
        else:
            df["porto_descarga"] = df["PORTO DE DESTINO"]
        # Quantidade: tente "QTDE FCL"; se não existir, use "QUANTIDADE TEUS"
        qtd_col = "QTDE FCL" if "QTDE FCL" in df.columns else "QUANTIDADE TEUS"
    else:
        st.error("Tipo de operação desconhecido.")
        return pd.DataFrame()
    
    # Padroniza a coluna de ano/mês: assumindo que existe "ANO/MÊS"
    if "ANO/MÊS" in df.columns:
        df["ano_mes"] = pd.to_numeric(df["ANO/MÊS"], errors="coerce")
    else:
        df["ano_mes"] = None

    # Converte a coluna de quantidade para float, tratando vírgulas e removendo espaços
    if qtd_col in df.columns:
        df[qtd_col] = df[qtd_col].astype(str).str.replace(",", ".").str.strip()
        df["qtd_container"] = pd.to_numeric(df[qtd_col], errors="coerce").fillna(0)
    else:
        df["qtd_container"] = 0

    # Seleciona apenas as colunas padronizadas
    df_padronizado = df[["cliente", "porto_descarga", "ano_mes", "qtd_container"]].copy()
    df_padronizado["tipo_operacao"] = tipo_operacao
    return df_padronizado

def carregar_planilhas():
    """
    Carrega integralmente as planilhas de importação, exportação e cabotagem, padronizando os dados.
    """
    try:
        df_import = pd.read_excel('importação.xlsx')
        df_export = pd.read_excel('exportação.xlsx')
        df_cabotagem = pd.read_excel('cabotagem.xlsx')
        
        df_import_pad = padronizar_planilha(df_import, "importacao")
        df_export_pad = padronizar_planilha(df_export, "exportacao")
        df_cabotagem_pad = padronizar_planilha(df_cabotagem, "cabotagem")
        
        # Concatena os três dataframes padronizados
        df_consolidado = pd.concat([df_import_pad, df_export_pad, df_cabotagem_pad], ignore_index=True)
        return df_consolidado
    except Exception as e:
        st.error(f"Erro ao carregar as planilhas: {e}")
        return pd.DataFrame()

def carregar_clientes():
    """
    Carrega o arquivo clientes.txt com os dados dos clientes.
    """
    try:
        with open("clientes.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.warning(f"Erro ao carregar clientes.txt: {e}")
        return ""

def gerar_resumo_dados(dados):
    """
    Gera um resumo detalhado dos dados consolidados, incluindo:
      - Número de registros
      - Lista de colunas
      - Amostra das primeiras 3 linhas (em formato markdown, se possível)
    """
    num_registros = len(dados)
    colunas = ', '.join(dados.columns)
    try:
        amostra = dados.head(3).to_markdown(index=False)
    except ImportError:
        amostra = dados.head(3).to_string(index=False)
    resumo = f"Número de registros: {num_registros}.\nColunas: {colunas}.\n\nExemplo de dados:\n{amostra}"
    return resumo

# =============================================================================
# As funções e trechos a seguir referentes à geração e demonstração de insights
# foram comentados conforme solicitado.
#
# def gerar_insights(dados_logisticos, dados_clientes):
#     """
#     Gera insights gerais usando o modelo GPT-4 com base em um resumo detalhado dos dados consolidados
#     e nas informações dos clientes.
#     O prompt inclui diretrizes estratégicas e de encaminhamento.
#     """
#     resumo_compacto = gerar_resumo_dados(dados_logisticos)
#     prompt_template = (
#         "Você é um analista especialista em logística portuária, comércio exterior e gestão de clientes.\n\n"
#         "Com base nos dados logísticos consolidados e nas informações dos clientes fornecidos, analise e sugira insights detalhados para aumentar a captação de novos clientes. Considere os seguintes pontos:\n"
#         "1. Segmentação Geográfica e de Operações: identifique as regiões com maior movimentação e infraestrutura local favorável.\n"
#         "2. Personalização das Propostas Comerciais: proponha soluções customizadas que integrem serviços de importação, exportação e cabotagem.\n"
#         "3. Aproveitamento das Facilidades Logísticas: destaque os diferenciais competitivos locais (acesso a portos, rastreamento em tempo real, capacidade de armazenagem, etc.).\n"
#         "4. Desenvolvimento de Parcerias Estratégicas: recomende parcerias com agentes de carga, operadoras logísticas e autoridades regionais.\n"
#         "5. Incentivos e Programas de Fidelização Regionais: sugira benefícios diferenciados conforme a região e o volume de operações.\n"
#         "6. Uso de Dados para Apoiar a Tomada de Decisão: indique a criação de dashboards e KPIs para monitorar os resultados.\n"
#         "7. Diretrizes para Encaminhamento: identifique quais clientes do arquivo possuem maior potencial e justifique os motivos com base nos dados logísticos.\n\n"
#         "Dados Logísticos (Resumo):\n{dados_logisticos}\n\n"
#         "Informações dos Clientes:\n{dados_clientes}\n\n"
#         "Insights:"
#     )
#     final_prompt = prompt_template.format(
#         dados_logisticos=resumo_compacto,
#         dados_clientes=dados_clientes
#     )
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "Você é um assistente analítico."},
#                 {"role": "user", "content": final_prompt}
#             ],
#             temperature=0.7,
#             max_tokens=512
#         )
#         return response['choices'][0]['message']['content']
#     except Exception as e:
#         st.error(f"Erro na geração dos insights: {e}")
#         return "Não foi possível gerar os insights no momento."
# =============================================================================

def responder_consulta_local(pergunta, df):
    """
    Tenta responder a perguntas específicas diretamente com pandas, lidando com os tipos de dados.
    Exemplo: "Qual empresa mais trouxe containers para o porto do Rio de Janeiro em fevereiro de 2025 e quantos foram?"
    """
    # Exemplo: se a pergunta contiver palavras-chave para análise do porto do Rio de Janeiro em fevereiro de 2025,
    # faz a análise local
    if ("rio de janeiro" in pergunta.lower() and 
        "fevereiro" in pergunta.lower() and 
        "2025" in pergunta):
        # Verifica se as colunas necessárias existem no DataFrame consolidado
        colunas_necessarias = ["porto_descarga", "ano_mes", "cliente", "qtd_container"]
        if not all(col in df.columns for col in colunas_necessarias):
            return "Os dados não contêm as colunas necessárias para essa análise."
        
        # Filtra para "Rio de Janeiro" no campo "porto_descarga"
        df_rj = df[df["porto_descarga"].str.contains("Rio de Janeiro", case=False, na=False)]
        # Filtra para fevereiro de 2025 (supondo que "ano_mes" esteja no formato YYYYMM, ex.: 202502)
        df_rj = df_rj[df_rj["ano_mes"] == 202502]
        
        if df_rj.empty:
            return "Nenhuma informação encontrada para o porto do Rio de Janeiro em fevereiro de 2025."
        
        # Agrupa por "cliente" e soma "qtd_container"
        grupo = df_rj.groupby("cliente")["qtd_container"].sum()
        if grupo.empty:
            return "Nenhuma informação encontrada após o agrupamento dos dados."
        
        max_val = grupo.max()
        empresa = grupo.idxmax()
        return (f"A empresa que mais trouxe containers para o porto do Rio de Janeiro em fevereiro de 2025 "
                f"foi {empresa}, com um total de {max_val:.0f} containers.")
    else:
        return None

def responder_pergunta(pergunta, dados_logisticos, dados_clientes, df):
    """
    Tenta primeiro responder a pergunta utilizando consulta local via pandas.
    Se não for aplicável, utiliza a API do OpenAI para responder com base em um prompt.
    """
    resposta_local = responder_consulta_local(pergunta, df)
    if resposta_local is not None and "Nenhuma informação" not in resposta_local:
        return resposta_local
    
    resumo_compacto = gerar_resumo_dados(dados_logisticos)
    prompt_template = (
        "Você é um analista especialista em logística portuária, comércio exterior e gestão de clientes.\n\n"
        "Com base nos dados logísticos e nas informações dos clientes fornecidos, responda de forma objetiva à seguinte pergunta:\n"
        "Pergunta: {pergunta}\n\n"
        "Dados Logísticos (Resumo):\n{dados_logisticos}\n\n"
        "Informações dos Clientes:\n{dados_clientes}\n\n"
        "Resposta:"
    )
    final_prompt = prompt_template.format(
        pergunta=pergunta,
        dados_logisticos=resumo_compacto,
        dados_clientes=dados_clientes
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um assistente analítico."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.7,
            max_tokens=256
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Erro ao responder a pergunta: {e}")
        return "Não foi possível responder a pergunta no momento."

# Configura a interface do Streamlit
st.set_page_config(page_title="Oráculo Comercial Autônomo", layout="wide")
st.title("🤖 Oráculo Comercial Autônomo")
st.markdown("Este oráculo analisa diariamente os dados logísticos e de clientes para responder perguntas específicas sobre as operações.")

with st.spinner("Carregando dados..."):
    df = carregar_planilhas()
    dados_clientes = carregar_clientes()
    
    if df.empty:
        st.error("Nenhum dado encontrado nas planilhas.")

# =============================================================================
# Bloco de geração e exibição de insights comentado conforme solicitado.
#
# with st.spinner("Carregando dados e gerando insights gerais..."):
#     if not df.empty:
#         insights = gerar_insights(df, dados_clientes)
#         st.subheader("💡 Insights do Dia")
#         st.write(insights)
#         
#         with st.expander("Ver resumo dos dados logísticos"):
#             resumo_exibicao = gerar_resumo_dados(df)
#             st.write(resumo_exibicao)
#         
#         hoje = datetime.date.today().isoformat()
#         os.makedirs("logs", exist_ok=True)
#         with open(f"logs/insights_{hoje}.txt", "w", encoding="utf-8") as f:
#             f.write(insights)
#         st.success(f"Insights salvos em logs/insights_{hoje}.txt")
#     else:
#         st.error("Nenhum dado encontrado nas planilhas.")
# =============================================================================

# Seção para perguntas específicas
st.markdown("### Faça uma pergunta sobre os dados")
pergunta = st.text_input("Digite sua pergunta:")

if pergunta:
    with st.spinner("Respondendo à pergunta..."):
        resposta = responder_pergunta(pergunta, df, dados_clientes, df)
        st.subheader("🔍 Resposta à pergunta")
        st.write(resposta)

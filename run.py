import os
import re
import streamlit as st
import pandas as pd
import datetime
import openai

# Configure sua chave de API do OpenAI
openai.api_key = "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"

def padronizar_planilha(df, tipo_operacao):
    """
    Padroniza o DataFrame de acordo com o tipo de operação (importação, exportação, cabotagem).
    Cria as colunas: "cliente", "porto", "ano_mes" e "qtd_container".
    - Converte a coluna de data "ANO/MÊS" para numérico (ex.: 202502 para fevereiro de 2025).
    - Converte a coluna de quantidade para numérico, tratando vírgulas.
    - Para exportação, tenta usar "PORTO EMBARQUE" se disponível; caso contrário, usa "PORTO DESTINO" ou "PORTO DESCARGA".
    """
    df = df.copy()
    if tipo_operacao == "importacao":
        df["cliente"] = df["CONSIGNATÁRIO"]
        df["porto_descarga"] = df["PORTO DESCARGA"]
        qtd_col = "QTDE CONTAINER"
    elif tipo_operacao == "exportacao":
        if "NOME EXPORTADOR" in df.columns:
            df["cliente"] = df["NOME EXPORTADOR"]
        else:
            df["cliente"] = df["CONSIGNATÁRIO"]
        # Para exportação, tente usar "PORTO EMBARQUE" se existir
        if "PORTO EMBARQUE" in df.columns:
            df["porto_embarque"] = df["PORTO EMBARQUE"]
        else:
            df["porto_embarque"] = df["PORTO DESTINO"] if "PORTO DESTINO" in df.columns else df["PORTO DESCARGA"]
        df["porto_descarga"] = df["porto_embarque"]
        qtd_col = "QTDE CONTEINER"  # Verifique a grafia conforme o arquivo
    elif tipo_operacao == "cabotagem":
        df["cliente"] = df["DESTINATÁRIO"]
        if "PORTO DE DESCARGA" in df.columns:
            df["porto_descarga"] = df["PORTO DE DESCARGA"]
        else:
            df["porto_descarga"] = df["PORTO DE DESTINO"]
        qtd_col = "QTDE FCL" if "QTDE FCL" in df.columns else "QUANTIDADE TEUS"
    else:
        st.error("Tipo de operação desconhecido.")
        return pd.DataFrame()
    
    # Cria uma coluna unificada "porto" a partir de "porto_descarga"
    df["porto"] = df["porto_descarga"]
    
    # Converte "ANO/MÊS" para numérico (formato YYYYMM, ex.: 202502 para fevereiro de 2025)
    if "ANO/MÊS" in df.columns:
        df["ano_mes"] = pd.to_numeric(df["ANO/MÊS"], errors="coerce")
    else:
        df["ano_mes"] = None
    
    # Converte a coluna de quantidade para float, tratando vírgulas e espaços
    if qtd_col in df.columns:
        df[qtd_col] = df[qtd_col].astype(str).str.replace(",", ".").str.strip()
        df["qtd_container"] = pd.to_numeric(df[qtd_col], errors="coerce").fillna(0)
    else:
        df["qtd_container"] = 0
        
    df_padronizado = df[["cliente", "porto", "ano_mes", "qtd_container"]].copy()
    df_padronizado["tipo_operacao"] = tipo_operacao
    return df_padronizado

def carregar_planilhas():
    """
    Carrega as planilhas de importação, exportação e cabotagem,
    padronizando os dados de cada uma e concatenando-os em um único DataFrame.
    """
    try:
        df_import = pd.read_excel('importação.xlsx')
        df_export = pd.read_excel('exportação.xlsx')
        df_cabotagem = pd.read_excel('cabotagem.xlsx')
        
        df_import_pad = padronizar_planilha(df_import, "importacao")
        df_export_pad = padronizar_planilha(df_export, "exportacao")
        df_cabotagem_pad = padronizar_planilha(df_cabotagem, "cabotagem")
        
        df_consolidado = pd.concat([df_import_pad, df_export_pad, df_cabotagem_pad], ignore_index=True)
        return df_consolidado
    except Exception as e:
        st.error(f"Erro ao carregar as planilhas: {e}")
        return pd.DataFrame()

def carregar_clientes():
    """
    Carrega o arquivo clientes.txt contendo informações adicionais dos clientes.
    """
    try:
        with open("clientes.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.warning(f"Erro ao carregar clientes.txt: {e}")
        return ""

def gerar_resumo_dados(dados):
    """
    Gera um resumo dos dados consolidados: número de registros, lista de colunas e uma amostra dos dados.
    """
    num_registros = len(dados)
    colunas = ', '.join(dados.columns)
    try:
        amostra = dados.head(3).to_markdown(index=False)
    except Exception:
        amostra = dados.head(3).to_string(index=False)
    resumo = f"Número de registros: {num_registros}.\nColunas: {colunas}.\n\nExemplo de dados:\n{amostra}"
    return resumo

def responder_consulta_local(pergunta, df):
    """
    Tenta responder perguntas específicas utilizando filtros aplicados sobre as colunas padronizadas.
    Essa função interpreta a pergunta para extrair condições (tipo de operação, ano, mês, cliente, porto)
    e, se identificar uma operação de agregação (por exemplo, "quantos", "total", "soma", "movimentou"),
    retorna o resultado da agregação.
    """
    pergunta_lower = pergunta.lower()
    filtro = pd.Series([True] * len(df))
    
    # Filtra por tipo de operação se mencionado (exportação, importação, cabotagem)
    if "export" in pergunta_lower:
        filtro &= df["tipo_operacao"].str.lower() == "exportacao"
    elif "import" in pergunta_lower:
        filtro &= df["tipo_operacao"].str.lower() == "importacao"
    elif "cabot" in pergunta_lower:
        filtro &= df["tipo_operacao"].str.lower() == "cabotagem"
    
    # Filtra por ano (formato numérico: YYYYMM)
    ano_match = re.search(r'\b(20\d{2})\b', pergunta_lower)
    if ano_match:
        ano = int(ano_match.group(1))
        filtro &= df["ano_mes"].notna() & ((df["ano_mes"] // 100) == ano)
    
    # Filtra por mês, se algum nome de mês for identificado
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }
    mes_encontrado = None
    for nome, num in meses.items():
        if nome in pergunta_lower:
            mes_encontrado = num
            break
    if mes_encontrado is not None:
        filtro &= df["ano_mes"].notna() & ((df["ano_mes"] % 100) == mes_encontrado)
    
    # Filtra por cliente se houver menção (procura pela substring no campo "cliente")
    clientes = df["cliente"].dropna().unique()
    cliente_encontrado = None
    for cl in clientes:
        if isinstance(cl, str) and cl.lower() in pergunta_lower:
            cliente_encontrado = cl
            break
    if cliente_encontrado:
        filtro &= df["cliente"].str.lower().str.contains(cliente_encontrado.lower(), na=False)
    
    # Filtra por porto usando a coluna unificada "porto"
    portos = df["porto"].dropna().unique()
    porto_encontrado = None
    for p in portos:
        if isinstance(p, str) and p.lower() in pergunta_lower:
            porto_encontrado = p
            break
    if porto_encontrado:
        filtro &= df["porto"].str.lower().str.contains(porto_encontrado.lower(), na=False)
    
    df_filtrado = df[filtro]
    if df_filtrado.empty:
        return "Nenhuma informação encontrada para os critérios informados."
    
    # Se a pergunta solicitar uma agregação de containers...
    if ("qual empresa" in pergunta_lower or ("empresa" in pergunta_lower and "mais" in pergunta_lower)):
        grupo = df_filtrado.groupby("cliente")["qtd_container"].sum()
        if grupo.empty:
            return "Nenhuma informação encontrada após o agrupamento dos dados."
        max_val = grupo.max()
        empresa = grupo.idxmax()
        return f"A empresa que mais trouxe containers foi {empresa}, com um total de {max_val:.0f} containers."
    elif any(kw in pergunta_lower for kw in ["quantos", "total", "soma", "movimentou", "número"]):
        total = df_filtrado["qtd_container"].sum()
        details = []
        if cliente_encontrado:
            details.append(f"para o consignatário {cliente_encontrado}")
        if porto_encontrado:
            details.append(f"no porto {porto_encontrado}")
        if ano_match:
            details.append(f"em {ano_match.group(1)}")
        if mes_encontrado:
            mes_nome = [nome for nome, num in meses.items() if num == mes_encontrado][0]
            details.append(f"em {mes_nome.capitalize()}")
        condicoes = ", ".join(details)
        return f"{condicoes.capitalize()} movimentou um total de {total:.0f} containers."
    else:
        # Se não houver indicação clara de agregação, retorna uma amostra dos registros filtrados
        return f"Registros encontrados:\n{df_filtrado.head(5).to_string(index=False)}"

def responder_pergunta(pergunta, dados_logisticos, dados_clientes, df):
    """
    Tenta primeiro responder a pergunta utilizando a consulta local (pandas).
    Se a resposta local não for satisfatória, utiliza a API do OpenAI para complementar a resposta.
    """
    resposta_local = responder_consulta_local(pergunta, df)
    if resposta_local and "Nenhuma informação" not in resposta_local:
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

# Configuração da interface do Streamlit
st.set_page_config(page_title="Oráculo Comercial Autônomo", layout="wide")
st.title("🤖 Oráculo Comercial Autônomo")
st.markdown("Este oráculo analisa diariamente os dados logísticos e de clientes para responder perguntas específicas sobre as operações.")

with st.spinner("Carregando dados..."):
    df = carregar_planilhas()
    dados_clientes = carregar_clientes()
    if df.empty:
        st.error("Nenhum dado encontrado nas planilhas.")

st.markdown("### Faça uma pergunta sobre os dados")
pergunta = st.text_input("Digite sua pergunta:")

if pergunta:
    with st.spinner("Respondendo à pergunta..."):
        resposta = responder_pergunta(pergunta, df, dados_clientes, df)
        st.subheader("🔍 Resposta à pergunta")
        st.write(resposta)

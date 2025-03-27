"""
Módulo responsável por gerar respostas usando a API OpenAI
"""
import os
import streamlit as st
from openai import OpenAI
from .filters import aplicar_filtros
from .data_processing import unificar_contagem_containers

def responder_pergunta(pergunta, df, filtros):
    """Gera uma resposta para a pergunta do usuário com base nos dados filtrados"""
    try:
        # Aplicar filtros aos dados
        df_filtrado = aplicar_filtros(df, filtros)
        
        if df_filtrado.empty:
            return "Não encontrei dados que correspondam aos critérios da sua pergunta. Por favor, verifique se os filtros estão corretos."
        
        # Calcular métricas relevantes
        total_containers = unificar_contagem_containers(df_filtrado, filtros)
        num_registros = len(df_filtrado)
        
        # Construir contexto para a API
        contexto = f"""
        Pergunta: {pergunta}
        
        Dados analisados:
        - Total de registros: {num_registros}
        - Total de containers: {total_containers}
        - Filtros aplicados: {filtros}
        """
        
        # Verificar se a chave da API está configurada
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not client.api_key:
            return " Chave da API OpenAI não configurada! Configure a variável de ambiente OPENAI_API_KEY"
        
        # Gerar resposta usando a API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Você é um assistente especializado em análise de dados logísticos.
                 Forneça respostas objetivas e diretas, focando nos números e insights mais relevantes."""},
                {"role": "user", "content": contexto}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Erro ao processar pergunta: {str(e)}")
        return f"Ocorreu um erro ao processar sua pergunta. Por favor, tente reformular ou entre em contato com o suporte. Detalhes: {str(e)}"

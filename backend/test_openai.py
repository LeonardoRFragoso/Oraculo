#!/usr/bin/env python3
"""
Script de teste para verificar conexão com OpenAI
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Carregar .env
load_dotenv('../.env')

api_key = os.getenv('OPENAI_API_KEY')

print(f"API Key encontrada: {'Sim' if api_key else 'Não'}")
print(f"Primeiros caracteres: {api_key[:20] if api_key else 'N/A'}...")

if api_key:
    try:
        print("\nTestando conexão com OpenAI...")
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "user", "content": "Responda apenas: OK"}
            ],
            max_tokens=10
        )
        
        answer = response.choices[0].message.content
        print(f"✓ Sucesso! Resposta: {answer}")
        
    except Exception as e:
        print(f"✗ Erro: {e}")
        print(f"Tipo: {type(e).__name__}")
else:
    print("✗ OPENAI_API_KEY não encontrada!")

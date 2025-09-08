@echo off
title GPTRACKER - Sistema Inteligente de Análise Comercial

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                        GPTRACKER                             ║
echo ║           Sistema Inteligente de Análise Comercial           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🔍 Verificando ambiente virtual...
if not exist venv (
    echo ❌ Ambiente virtual não encontrado!
    echo 🔧 Execute setup.bat primeiro para configurar o projeto.
    pause
    exit /b 1
)

echo ⚡ Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo 🚀 Iniciando GPTRACKER...
echo.
echo 📊 Dashboard disponível em: http://localhost:8501
echo 💬 Chat GPT integrado com seus dados
echo ☁️ Integração universal com nuvem
echo 🎯 Gestão de budget e metas
echo.

streamlit run gptracker_main.py

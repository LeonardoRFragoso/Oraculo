@echo off
echo Iniciando GPTRACKER Chat Simples...
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Iniciando GPTRACKER Chat...
echo Acesse: http://localhost:8501
echo.

streamlit run gptracker_simple.py --server.port 8501

pause

@echo off
echo 🚀 Configurando GPTRACKER...

echo 📁 Removendo ambiente virtual antigo...
if exist venv rmdir /s /q venv

echo 🔧 Criando novo ambiente virtual...
python -m venv venv

echo ⚡ Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo 📦 Atualizando pip...
python -m pip install --upgrade pip

echo 📚 Instalando dependências...
pip install -r requirements.txt

echo ✅ Configuração concluída!
echo.
echo 🎯 Para executar o GPTRACKER:
echo    1. .\venv\Scripts\activate
echo    2. streamlit run gptracker_main.py
echo.
pause

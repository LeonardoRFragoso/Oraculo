#!/bin/bash

# Script de instalação otimizada para servidor
echo "🚀 Instalando GPTracker no servidor..."

# Limpar cache do pip para liberar espaço
echo "🧹 Limpando cache do pip..."
pip cache purge

# Verificar espaço disponível
echo "💾 Espaço disponível:"
df -h /tmp
df -h .

# Instalar PyTorch CPU-only primeiro (evita download CUDA)
echo "🔧 Instalando PyTorch CPU-only..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar dependências básicas sem ML pesado
echo "📦 Instalando dependências básicas..."
pip install -r requirements-cpu-only.txt

# Instalar ML libraries uma por vez para controlar espaço
echo "🤖 Instalando bibliotecas ML..."
pip install scikit-learn>=1.3.0
pip install transformers>=4.30.0
pip install tokenizers>=0.13.0

# Verificar se tudo foi instalado
echo "✅ Verificando instalação..."
python -c "import streamlit; import pandas; import openai; print('✅ Dependências principais OK')"

echo "🎉 Instalação concluída!"
echo "Para executar: streamlit run gptracker.py --server.port 8598"

# 🤖 Oráculo - Sistema de Análise de Dados Logísticos

Sistema de análise de dados logísticos com interface conversacional usando Streamlit e OpenAI GPT-4.

## 📋 Estrutura do Projeto

```
.
├── src/
│   ├── __init__.py
│   ├── api_response.py      # Interação com a API OpenAI
│   ├── context_builder.py   # Construção do contexto para a API
│   ├── data_loader.py       # Carregamento e cache de dados
│   ├── data_processing.py   # Processamento e normalização dos dados
│   ├── filters.py          # Aplicação de filtros aos dados
│   └── query_interpreter.py # Interpretação de perguntas
├── run3.py                 # Aplicação principal
├── requirements.txt        # Dependências do projeto
└── README.md              # Este arquivo
```

## 🚀 Requisitos

- Python 3.8+
- Dependências listadas em requirements.txt
- Arquivo de dados consolidados (dados_consolidados.xlsx)
- Chave de API da OpenAI

## 🚀 Configuração

1. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

2. **Configure a chave da API OpenAI**:
```bash
export OPENAI_API_KEY=sua-chave-aqui
```

## 💡 Uso

Execute a aplicação com:
```bash
streamlit run run3.py
```

A interface web será aberta automaticamente no seu navegador.

## 📊 Funcionalidades

- Análise de dados de importação, exportação e cabotagem
- Contagem unificada de containers
- Filtragem por:
  - Tipo de operação
  - Período (ano/mês)
  - Porto
  - Cliente
- Interface conversacional natural
- Respostas contextualizadas usando GPT-4

## 📈 Manutenção

O código foi modularizado para facilitar a manutenção e extensão. Cada módulo tem uma responsabilidade específica:

- `data_processing.py`: Normalização e processamento dos dados
- `query_interpreter.py`: Interpretação de perguntas em linguagem natural
- `filters.py`: Aplicação de filtros aos dados
- `context_builder.py`: Construção do contexto para a API
- `api_response.py`: Interação com a API OpenAI
- `data_loader.py`: Carregamento e cache de dados

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Faça commit das suas alterações
4. Faça push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença [INSERIR_LICENÇA].

# 🚀 Guia de Instalação e Configuração - GPTRACKER

## 📋 Pré-requisitos

### Sistema Operacional
- Windows 10/11, macOS 10.14+, ou Linux Ubuntu 18.04+
- Mínimo 4GB RAM, recomendado 8GB+
- 2GB de espaço livre em disco

### Software Necessário
- **Python 3.8 ou superior** ([Download aqui](https://python.org/downloads/))
- **Git** ([Download aqui](https://git-scm.com/downloads/))
- **Chave API OpenAI** ([Obter aqui](https://platform.openai.com/api-keys))

## 🔧 Instalação Passo a Passo

### 1. Preparação do Ambiente

```bash
# Verificar versão do Python
python --version

# Criar diretório do projeto
mkdir gptracker
cd gptracker

# Clonar repositório (se aplicável)
git clone <url-do-repositorio> .
```

### 2. Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

### 3. Instalação de Dependências

```bash
# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
```

### 4. Configuração de Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# API Keys
OPENAI_API_KEY=sk-sua-chave-openai-aqui

# Segurança
JWT_SECRET_KEY=sua-chave-jwt-muito-secreta-aqui

# Configurações da API
API_PORT=5000
FLASK_ENV=development

# Configurações opcionais
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
```

### 5. Estrutura de Diretórios

```bash
# Criar diretórios necessários
mkdir -p dados/processed
mkdir -p dados/raw
mkdir -p dados/archive
mkdir -p backups
mkdir -p uploads
mkdir -p logs
```

### 6. Dados Iniciais

Coloque seu arquivo principal de dados:
- `dados/Dados_Consolidados.xlsx` - Arquivo principal com dados logísticos

## ▶️ Executando o Sistema

### Método 1: Interface Web (Recomendado)

```bash
# Ativar ambiente virtual (se não estiver ativo)
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Executar GPTRACKER
streamlit run gptracker_main.py
```

O sistema abrirá automaticamente no navegador em `http://localhost:8501`

### Método 2: API REST

```bash
# Em um terminal separado
python src/api_server.py
```

A API estará disponível em `http://localhost:5000`

## 👤 Primeiro Acesso

### Usuários Padrão

O sistema cria automaticamente os seguintes usuários:

| Usuário | Senha | Perfil | Descrição |
|---------|-------|--------|-----------|
| `admin` | `admin123` | Administrador | Acesso total ao sistema |
| `comercial` | `comercial123` | Comercial | Acesso a dados comerciais e budget |
| `operacional` | `operacional123` | Operacional | Acesso a dados operacionais |

### Primeiro Login

1. Acesse `http://localhost:8501`
2. Use `admin` / `admin123` para primeiro acesso
3. **IMPORTANTE**: Altere as senhas padrão imediatamente

## 🔧 Configurações Avançadas

### Performance

Para melhor performance com grandes volumes de dados:

```env
# Adicionar ao .env
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200
```

### Segurança em Produção

```env
# Configurações de produção
FLASK_ENV=production
JWT_ACCESS_TOKEN_EXPIRES=3600
STREAMLIT_SERVER_HEADLESS=true
```

### Configuração de Banco de Dados (Opcional)

Para usar banco de dados PostgreSQL:

```bash
pip install psycopg2-binary
```

```env
DATABASE_URL=postgresql://user:password@localhost:5432/gptracker
```

## 📊 Configuração de Dados

### Formatos Suportados

- **Excel**: `.xlsx`, `.xls`
- **CSV**: `.csv`
- **JSON**: `.json`
- **Parquet**: `.parquet`

### Estrutura de Dados Esperada

#### Dados Logísticos
```
Colunas obrigatórias:
- qtd_container (numérico)
- cliente (texto)
- ano_mes (YYYYMM)

Colunas opcionais:
- tipo_operacao
- porto
- armador
- navio
```

#### Dados Comerciais
```
Colunas obrigatórias:
- cliente (texto)
- receita (numérico)
- periodo (YYYYMM)

Colunas opcionais:
- vendedor
- regiao
- produto
```

## 🚨 Solução de Problemas

### Erro: "ModuleNotFoundError"
```bash
# Verificar se ambiente virtual está ativo
which python  # Linux/macOS
where python   # Windows

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Erro: "OpenAI API Key not found"
```bash
# Verificar arquivo .env
cat .env  # Linux/macOS
type .env # Windows

# Verificar variável de ambiente
echo $OPENAI_API_KEY  # Linux/macOS
echo %OPENAI_API_KEY% # Windows
```

### Erro: "Permission denied"
```bash
# Linux/macOS - ajustar permissões
chmod +x gptracker_main.py
chmod 755 src/
```

### Erro: "Port already in use"
```bash
# Verificar processos usando a porta
lsof -i :8501  # Linux/macOS
netstat -ano | findstr :8501  # Windows

# Usar porta diferente
streamlit run gptracker_main.py --server.port 8502
```

### Erro de Memória
```bash
# Aumentar limite de memória do Python
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
```

## 🔄 Atualizações

### Atualizar Dependências
```bash
pip install -r requirements.txt --upgrade
```

### Backup de Dados
```bash
# Criar backup manual
cp -r dados/ backup_$(date +%Y%m%d)/
```

### Logs do Sistema
```bash
# Verificar logs
tail -f logs/security_audit.log
tail -f logs/system.log
```

## 📞 Suporte

### Logs Importantes
- `logs/security_audit.log` - Auditoria de segurança
- `logs/system.log` - Logs do sistema
- `logs/errors.log` - Erros da aplicação

### Diagnóstico
```bash
# Verificar status do sistema
python -c "import streamlit; print('Streamlit OK')"
python -c "import openai; print('OpenAI OK')"
python -c "import pandas; print('Pandas OK')"
```

### Informações do Sistema
```bash
# Versões instaladas
pip list | grep -E "(streamlit|openai|pandas)"

# Informações do Python
python -c "import sys; print(sys.version)"
```

## ✅ Checklist de Instalação

- [ ] Python 3.8+ instalado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas sem erros
- [ ] Arquivo `.env` configurado com API key
- [ ] Estrutura de diretórios criada
- [ ] Dados principais carregados
- [ ] Sistema executando em `http://localhost:8501`
- [ ] Login realizado com sucesso
- [ ] Senhas padrão alteradas

## 🎯 Próximos Passos

1. **Configurar Metas**: Acesse Budget & Metas
2. **Carregar Dados**: Use Gestão de Dados para upload
3. **Explorar Chat**: Faça perguntas sobre seus dados
4. **Configurar Usuários**: Adicione usuários específicos
5. **Agendar Backups**: Configure rotina de backup

---

**Instalação concluída com sucesso!** 🎉

Para suporte adicional, consulte a documentação completa no `README.md`

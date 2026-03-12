#!/bin/bash

# ============================================
# GPTRACKER - Script de Setup do OpenRAG
# ============================================

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║         GPTRACKER - Setup OpenRAG                             ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para printar com cor
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Verificar se Docker está instalado
check_docker() {
    print_info "Verificando Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker não encontrado. Por favor, instale o Docker primeiro."
        exit 1
    fi
    print_success "Docker encontrado: $(docker --version)"
}

# Verificar se Docker Compose está instalado
check_docker_compose() {
    print_info "Verificando Docker Compose..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro."
        exit 1
    fi
    print_success "Docker Compose encontrado"
}

# Verificar requisitos de sistema
check_system_requirements() {
    print_info "Verificando requisitos do sistema..."
    
    # Verificar memória disponível (mínimo 8GB recomendado)
    total_mem=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_mem" -lt 8 ]; then
        print_warning "Memória disponível: ${total_mem}GB (recomendado: 8GB+)"
    else
        print_success "Memória disponível: ${total_mem}GB"
    fi
    
    # Verificar espaço em disco (mínimo 20GB recomendado)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 20 ]; then
        print_warning "Espaço em disco: ${available_space}GB (recomendado: 20GB+)"
    else
        print_success "Espaço em disco: ${available_space}GB"
    fi
}

# Configurar vm.max_map_count para OpenSearch
configure_opensearch() {
    print_info "Configurando vm.max_map_count para OpenSearch..."
    
    current_value=$(sysctl vm.max_map_count | awk '{print $3}')
    required_value=262144
    
    if [ "$current_value" -lt "$required_value" ]; then
        print_warning "vm.max_map_count atual: $current_value (requerido: $required_value)"
        
        if [ "$EUID" -eq 0 ]; then
            sysctl -w vm.max_map_count=$required_value
            echo "vm.max_map_count=$required_value" >> /etc/sysctl.conf
            print_success "vm.max_map_count configurado para $required_value"
        else
            print_warning "Execute como root para configurar automaticamente, ou execute:"
            echo "  sudo sysctl -w vm.max_map_count=$required_value"
            echo "  echo 'vm.max_map_count=$required_value' | sudo tee -a /etc/sysctl.conf"
        fi
    else
        print_success "vm.max_map_count já configurado: $current_value"
    fi
}

# Criar arquivo .env se não existir
setup_env_file() {
    print_info "Configurando arquivo .env..."
    
    if [ ! -f .env ]; then
        if [ -f .env.openrag.example ]; then
            cp .env.openrag.example .env
            print_success "Arquivo .env criado a partir do exemplo"
            print_warning "IMPORTANTE: Edite o arquivo .env e configure sua OPENAI_API_KEY"
        else
            print_error "Arquivo .env.openrag.example não encontrado"
            exit 1
        fi
    else
        print_success "Arquivo .env já existe"
    fi
}

# Criar diretórios necessários
create_directories() {
    print_info "Criando diretórios necessários..."
    
    mkdir -p dados/processed
    mkdir -p dados/raw
    mkdir -p dados/archive
    mkdir -p dados/chat_history
    mkdir -p logs
    mkdir -p backups
    mkdir -p langflow_workflows
    
    print_success "Diretórios criados"
}

# Baixar imagens Docker
pull_docker_images() {
    print_info "Baixando imagens Docker (isso pode levar alguns minutos)..."
    
    docker-compose -f docker-compose.openrag.yml pull
    
    print_success "Imagens Docker baixadas"
}

# Iniciar serviços
start_services() {
    print_info "Iniciando serviços OpenRAG..."
    
    docker-compose -f docker-compose.openrag.yml up -d
    
    print_success "Serviços iniciados"
}

# Aguardar serviços ficarem prontos
wait_for_services() {
    print_info "Aguardando serviços ficarem prontos..."
    
    max_attempts=30
    attempt=0
    
    # Aguardar OpenSearch
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
            print_success "OpenSearch está pronto"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "OpenSearch não ficou pronto a tempo"
        exit 1
    fi
    
    # Aguardar Langflow
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:7860/health > /dev/null 2>&1; then
            print_success "Langflow está pronto"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Langflow não ficou pronto a tempo"
        exit 1
    fi
}

# Mostrar status dos serviços
show_services_status() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    SERVIÇOS OPENRAG                           ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    
    docker-compose -f docker-compose.openrag.yml ps
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    ACESSO AOS SERVIÇOS                        ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Langflow (Workflow Builder):    http://localhost:7860"
    echo "🔍 OpenSearch:                     http://localhost:9200"
    echo "📊 OpenSearch Dashboards:          http://localhost:5601"
    echo "📄 Docling (Document Parser):      http://localhost:5001"
    echo "💾 Redis:                          localhost:6379"
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    PRÓXIMOS PASSOS                            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "1. Configure sua OPENAI_API_KEY no arquivo .env"
    echo "2. Execute a migração de dados:"
    echo "   python scripts/migrate_to_openrag.py"
    echo "3. Inicie o GPTRACKER:"
    echo "   streamlit run gptracker.py"
    echo ""
}

# Função principal
main() {
    check_docker
    check_docker_compose
    check_system_requirements
    configure_opensearch
    setup_env_file
    create_directories
    pull_docker_images
    start_services
    wait_for_services
    show_services_status
    
    print_success "Setup do OpenRAG concluído com sucesso!"
}

# Executar
main

# Makefile para GPTRACKER

.PHONY: help install setup-openrag migrate test validate clean docker-up docker-down

help:
	@echo "GPTRACKER - Comandos Disponíveis"
	@echo "================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install         - Instalar dependências Python"
	@echo "  make setup-openrag   - Configurar e iniciar OpenRAG"
	@echo "  make migrate         - Migrar dados para OpenRAG"
	@echo ""
	@echo "Testes:"
	@echo "  make test            - Executar testes automatizados"
	@echo "  make validate        - Validar instalação OpenRAG"
	@echo "  make test-coverage   - Executar testes com cobertura"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up       - Iniciar serviços OpenRAG"
	@echo "  make docker-down     - Parar serviços OpenRAG"
	@echo "  make docker-logs     - Ver logs dos serviços"
	@echo "  make docker-restart  - Reiniciar serviços"
	@echo ""
	@echo "Desenvolvimento:"
	@echo "  make run             - Iniciar GPTRACKER"
	@echo "  make clean           - Limpar arquivos temporários"
	@echo "  make lint            - Verificar código com flake8"
	@echo ""

install:
	@echo "📦 Instalando dependências..."
	pip install -r requirements.txt
	pip install -r requirements-openrag.txt
	pip install -r requirements-server.txt
	@echo "✅ Dependências instaladas!"

setup-openrag:
	@echo "🚀 Configurando OpenRAG..."
	chmod +x scripts/setup_openrag.sh
	./scripts/setup_openrag.sh
	@echo "✅ OpenRAG configurado!"

migrate:
	@echo "📦 Migrando dados para OpenRAG..."
	python scripts/migrate_to_openrag.py
	@echo "✅ Migração concluída!"

test:
	@echo "🧪 Executando testes..."
	pytest tests/ -v
	@echo "✅ Testes concluídos!"

test-coverage:
	@echo "🧪 Executando testes com cobertura..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "✅ Relatório de cobertura gerado em htmlcov/"

validate:
	@echo "✅ Validando instalação OpenRAG..."
	python scripts/validate_openrag.py
	@echo "✅ Validação concluída!"

docker-up:
	@echo "🐳 Iniciando serviços OpenRAG..."
	docker-compose -f docker-compose.openrag.yml up -d
	@echo "✅ Serviços iniciados!"
	@echo ""
	@echo "Acesse:"
	@echo "  - Langflow: http://localhost:7860"
	@echo "  - OpenSearch: http://localhost:9200"
	@echo "  - Dashboards: http://localhost:5601"

docker-down:
	@echo "🐳 Parando serviços OpenRAG..."
	docker-compose -f docker-compose.openrag.yml down
	@echo "✅ Serviços parados!"

docker-logs:
	@echo "📋 Logs dos serviços..."
	docker-compose -f docker-compose.openrag.yml logs -f

docker-restart:
	@echo "🔄 Reiniciando serviços..."
	docker-compose -f docker-compose.openrag.yml restart
	@echo "✅ Serviços reiniciados!"

docker-status:
	@echo "📊 Status dos serviços..."
	docker-compose -f docker-compose.openrag.yml ps

run:
	@echo "🚀 Iniciando GPTRACKER..."
	streamlit run gptracker.py

clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "✅ Limpeza concluída!"

lint:
	@echo "🔍 Verificando código..."
	flake8 src/ --max-line-length=120 --ignore=E501,W503
	@echo "✅ Verificação concluída!"

backup:
	@echo "💾 Criando backup..."
	mkdir -p backups
	tar -czf backups/gptracker_backup_$$(date +%Y%m%d_%H%M%S).tar.gz \
		dados/ src/ *.py requirements*.txt .env 2>/dev/null || true
	@echo "✅ Backup criado em backups/"

# Atalhos
up: docker-up
down: docker-down
logs: docker-logs
status: docker-status

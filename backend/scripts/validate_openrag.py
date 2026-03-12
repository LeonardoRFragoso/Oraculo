#!/usr/bin/env python3
"""
Script de validação pós-migração OpenRAG
Verifica se todos os serviços estão funcionando corretamente
"""
import sys
import os
import time
from pathlib import Path
from datetime import datetime
import pandas as pd

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.openrag_integration import OpenRAGManager, HybridLLMManager


class OpenRAGValidator:
    """Validador de instalação e migração OpenRAG"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'skipped': []
        }
        self.start_time = datetime.now()
    
    def print_header(self, text):
        """Imprime cabeçalho formatado"""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)
    
    def print_test(self, name, status, message=""):
        """Imprime resultado de teste"""
        symbols = {
            'pass': '✅',
            'fail': '❌',
            'warn': '⚠️',
            'skip': '⏭️',
            'info': 'ℹ️'
        }
        symbol = symbols.get(status, '•')
        print(f"{symbol} {name}")
        if message:
            print(f"   {message}")
    
    def test_environment_variables(self):
        """Testa variáveis de ambiente"""
        self.print_header("1. VARIÁVEIS DE AMBIENTE")
        
        required_vars = ['OPENAI_API_KEY']
        optional_vars = [
            'USE_OPENRAG',
            'OPENRAG_API_URL',
            'OPENSEARCH_URL',
            'OPENRAG_INDEX_NAME'
        ]
        
        # Verificar obrigatórias
        for var in required_vars:
            value = os.getenv(var)
            if value:
                self.print_test(f"{var}", 'pass', f"Configurada")
                self.results['passed'].append(f"env_{var}")
            else:
                self.print_test(f"{var}", 'fail', "NÃO configurada")
                self.results['failed'].append(f"env_{var}")
        
        # Verificar opcionais
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                self.print_test(f"{var}", 'pass', f"= {value}")
                self.results['passed'].append(f"env_{var}")
            else:
                self.print_test(f"{var}", 'warn', "Usando valor padrão")
                self.results['warnings'].append(f"env_{var}")
    
    def test_openrag_services(self):
        """Testa serviços OpenRAG"""
        self.print_header("2. SERVIÇOS OPENRAG")
        
        try:
            manager = OpenRAGManager()
            health = manager.health_check()
            
            # Verificar Langflow
            if health.get('langflow'):
                self.print_test("Langflow", 'pass', "http://localhost:7860")
                self.results['passed'].append('service_langflow')
            else:
                self.print_test("Langflow", 'fail', "Não acessível")
                self.results['failed'].append('service_langflow')
            
            # Verificar OpenSearch
            if health.get('opensearch'):
                self.print_test("OpenSearch", 'pass', "http://localhost:9200")
                self.results['passed'].append('service_opensearch')
            else:
                self.print_test("OpenSearch", 'fail', "Não acessível")
                self.results['failed'].append('service_opensearch')
            
            # Status geral
            if health.get('overall'):
                self.print_test("Status Geral", 'pass', "Todos os serviços OK")
                self.results['passed'].append('service_overall')
            else:
                self.print_test("Status Geral", 'fail', "Alguns serviços indisponíveis")
                self.results['failed'].append('service_overall')
                
        except Exception as e:
            self.print_test("Conexão OpenRAG", 'fail', f"Erro: {str(e)}")
            self.results['failed'].append('service_connection')
    
    def test_hybrid_manager(self):
        """Testa HybridLLMManager"""
        self.print_header("3. GERENCIADOR HÍBRIDO")
        
        try:
            manager = HybridLLMManager()
            
            self.print_test("Inicialização", 'pass', "HybridLLMManager criado")
            self.results['passed'].append('hybrid_init')
            
            # Verificar qual sistema está sendo usado
            if manager.use_openrag:
                self.print_test("Sistema Ativo", 'pass', "OpenRAG (moderno)")
                self.results['passed'].append('hybrid_openrag')
            else:
                self.print_test("Sistema Ativo", 'warn', "Sistema Legado (FAISS)")
                self.results['warnings'].append('hybrid_legacy')
                
        except Exception as e:
            self.print_test("HybridLLMManager", 'fail', f"Erro: {str(e)}")
            self.results['failed'].append('hybrid_error')
    
    def test_data_ingestion(self):
        """Testa ingestão de dados"""
        self.print_header("4. INGESTÃO DE DADOS")
        
        try:
            manager = OpenRAGManager()
            
            # Criar DataFrame de teste
            test_df = pd.DataFrame({
                'cliente': ['TEST_CLIENT'],
                'qtd_container': [10],
                'ano_mes': ['202503'],
                'test': [True]
            })
            
            self.print_test("DataFrame de Teste", 'pass', "Criado com 1 registro")
            
            # Tentar ingerir
            result = manager.ingest_dataframe(
                test_df,
                metadata={'source': 'validation_test', 'timestamp': datetime.now().isoformat()}
            )
            
            if result.get('success'):
                docs = result.get('documents_indexed', 0)
                self.print_test("Ingestão", 'pass', f"{docs} documentos indexados")
                self.results['passed'].append('ingestion_success')
            else:
                error = result.get('error', 'Erro desconhecido')
                self.print_test("Ingestão", 'fail', f"Erro: {error}")
                self.results['failed'].append('ingestion_failed')
                
        except Exception as e:
            self.print_test("Ingestão de Dados", 'fail', f"Erro: {str(e)}")
            self.results['failed'].append('ingestion_error')
    
    def test_search(self):
        """Testa busca semântica"""
        self.print_header("5. BUSCA SEMÂNTICA")
        
        try:
            manager = OpenRAGManager()
            
            # Busca simples
            start_time = time.time()
            results = manager.search(query="containers", top_k=5)
            elapsed = time.time() - start_time
            
            self.print_test("Busca Básica", 'pass', f"{len(results)} resultados em {elapsed:.3f}s")
            self.results['passed'].append('search_basic')
            
            # Busca com filtros
            results_filtered = manager.search(
                query="containers",
                filters={'test': True},
                top_k=3,
                rerank=True,
                hybrid=True
            )
            
            self.print_test("Busca Híbrida", 'pass', f"{len(results_filtered)} resultados")
            self.results['passed'].append('search_hybrid')
            
            # Verificar performance
            if elapsed < 1.0:
                self.print_test("Performance", 'pass', f"Busca rápida ({elapsed:.3f}s < 1s)")
                self.results['passed'].append('search_performance')
            else:
                self.print_test("Performance", 'warn', f"Busca lenta ({elapsed:.3f}s)")
                self.results['warnings'].append('search_slow')
                
        except Exception as e:
            self.print_test("Busca Semântica", 'fail', f"Erro: {str(e)}")
            self.results['failed'].append('search_error')
    
    def test_chat(self):
        """Testa chat com RAG"""
        self.print_header("6. CHAT COM RAG")
        
        try:
            manager = OpenRAGManager()
            
            # Chat simples
            start_time = time.time()
            response = manager.chat(
                query="Quantos containers foram movimentados?",
                model="gpt-4-turbo",
                temperature=0.7,
                max_tokens=500
            )
            elapsed = time.time() - start_time
            
            if isinstance(response, str) and len(response) > 0:
                self.print_test("Chat Básico", 'pass', f"Resposta gerada em {elapsed:.2f}s")
                self.print_test("Resposta", 'info', f"{response[:100]}...")
                self.results['passed'].append('chat_basic')
            else:
                self.print_test("Chat Básico", 'fail', "Resposta vazia ou inválida")
                self.results['failed'].append('chat_empty')
                
        except Exception as e:
            self.print_test("Chat com RAG", 'fail', f"Erro: {str(e)}")
            self.results['failed'].append('chat_error')
    
    def test_statistics(self):
        """Testa obtenção de estatísticas"""
        self.print_header("7. ESTATÍSTICAS DO ÍNDICE")
        
        try:
            manager = OpenRAGManager()
            stats = manager.get_stats()
            
            if 'error' not in stats:
                self.print_test("Estatísticas", 'pass', "Obtidas com sucesso")
                
                # Mostrar estatísticas
                for key, value in stats.items():
                    self.print_test(f"  {key}", 'info', str(value))
                
                self.results['passed'].append('stats_success')
            else:
                self.print_test("Estatísticas", 'warn', f"Erro: {stats['error']}")
                self.results['warnings'].append('stats_error')
                
        except Exception as e:
            self.print_test("Estatísticas", 'fail', f"Erro: {str(e)}")
            self.results['failed'].append('stats_failed')
    
    def test_legacy_compatibility(self):
        """Testa compatibilidade com sistema legado"""
        self.print_header("8. COMPATIBILIDADE LEGADO")
        
        try:
            # Verificar se arquivos legados existem
            legacy_files = {
                'documents.pkl': Path('documents.pkl'),
                'vector_index.faiss': Path('vector_index.faiss')
            }
            
            for name, path in legacy_files.items():
                if path.exists():
                    size = path.stat().st_size / (1024 * 1024)  # MB
                    self.print_test(f"{name}", 'pass', f"Existe ({size:.2f} MB)")
                    self.results['passed'].append(f'legacy_{name}')
                else:
                    self.print_test(f"{name}", 'info', "Não encontrado (normal após migração)")
                    self.results['skipped'].append(f'legacy_{name}')
                    
        except Exception as e:
            self.print_test("Compatibilidade", 'warn', f"Erro: {str(e)}")
            self.results['warnings'].append('legacy_error')
    
    def generate_report(self):
        """Gera relatório final"""
        self.print_header("RELATÓRIO FINAL")
        
        elapsed = datetime.now() - self.start_time
        
        total_tests = (
            len(self.results['passed']) +
            len(self.results['failed']) +
            len(self.results['warnings']) +
            len(self.results['skipped'])
        )
        
        print(f"\n📊 Resumo da Validação:")
        print(f"   ✅ Passou: {len(self.results['passed'])}")
        print(f"   ❌ Falhou: {len(self.results['failed'])}")
        print(f"   ⚠️  Avisos: {len(self.results['warnings'])}")
        print(f"   ⏭️  Pulados: {len(self.results['skipped'])}")
        print(f"   📝 Total: {total_tests}")
        print(f"   ⏱️  Tempo: {elapsed.total_seconds():.2f}s")
        
        # Determinar status geral
        if len(self.results['failed']) == 0:
            if len(self.results['warnings']) == 0:
                print("\n🎉 STATUS: PERFEITO - Todos os testes passaram!")
                return 0
            else:
                print("\n✅ STATUS: BOM - Testes passaram com avisos")
                return 0
        else:
            print("\n❌ STATUS: FALHOU - Alguns testes falharam")
            print("\n🔧 Ações Recomendadas:")
            
            if 'service_langflow' in self.results['failed']:
                print("   • Iniciar Langflow: docker-compose -f docker-compose.openrag.yml up -d langflow")
            
            if 'service_opensearch' in self.results['failed']:
                print("   • Iniciar OpenSearch: docker-compose -f docker-compose.openrag.yml up -d opensearch")
                print("   • Verificar vm.max_map_count: sudo sysctl -w vm.max_map_count=262144")
            
            if 'env_OPENAI_API_KEY' in self.results['failed']:
                print("   • Configurar OPENAI_API_KEY no arquivo .env")
            
            return 1
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         GPTRACKER - Validação OpenRAG                         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        
        self.test_environment_variables()
        self.test_openrag_services()
        self.test_hybrid_manager()
        self.test_data_ingestion()
        self.test_search()
        self.test_chat()
        self.test_statistics()
        self.test_legacy_compatibility()
        
        return self.generate_report()


def main():
    """Função principal"""
    validator = OpenRAGValidator()
    exit_code = validator.run_all_tests()
    
    print("\n" + "=" * 70)
    print("Validação concluída!")
    print("=" * 70 + "\n")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Testes automatizados para integração OpenRAG
"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.openrag_integration import OpenRAGManager, HybridLLMManager


class TestOpenRAGManager:
    """Testes para OpenRAGManager"""
    
    @pytest.fixture
    def manager(self):
        """Fixture para criar manager"""
        return OpenRAGManager()
    
    @pytest.fixture
    def sample_dataframe(self):
        """Fixture com DataFrame de exemplo"""
        return pd.DataFrame({
            'cliente': ['MICHELIN', 'GOODYEAR', 'PIRELLI'],
            'qtd_container': [100, 50, 75],
            'ano_mes': ['202503', '202503', '202503'],
            'porto': ['SANTOS', 'PARANAGUA', 'SANTOS']
        })
    
    def test_health_check(self, manager):
        """Testa verificação de saúde dos serviços"""
        health = manager.health_check()
        
        assert isinstance(health, dict)
        assert 'langflow' in health
        assert 'opensearch' in health
        assert 'overall' in health
        assert isinstance(health['overall'], bool)
    
    def test_ingest_dataframe(self, manager, sample_dataframe):
        """Testa ingestão de DataFrame"""
        result = manager.ingest_dataframe(
            sample_dataframe,
            metadata={'source': 'test', 'test_run': True}
        )
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert 'documents_indexed' in result
            assert result['documents_indexed'] > 0
    
    def test_ingest_empty_dataframe(self, manager):
        """Testa ingestão de DataFrame vazio"""
        empty_df = pd.DataFrame()
        result = manager.ingest_dataframe(empty_df)
        
        assert isinstance(result, dict)
        assert result['success'] == False
        assert 'error' in result
    
    def test_df_to_documents(self, manager, sample_dataframe):
        """Testa conversão de DataFrame para documentos"""
        documents = manager._df_to_documents(
            sample_dataframe,
            metadata={'source': 'test'}
        )
        
        assert isinstance(documents, list)
        assert len(documents) > 0
        
        # Verificar estrutura dos documentos
        for doc in documents:
            assert 'content' in doc
            assert 'metadata' in doc
            assert isinstance(doc['metadata'], dict)
    
    def test_search(self, manager):
        """Testa busca semântica"""
        results = manager.search(
            query="containers",
            top_k=5,
            rerank=False
        )
        
        assert isinstance(results, list)
        # Pode estar vazio se índice não tiver dados
    
    def test_search_with_filters(self, manager):
        """Testa busca com filtros"""
        results = manager.search(
            query="containers Michelin",
            filters={'cliente': 'MICHELIN'},
            top_k=3,
            rerank=True,
            hybrid=True
        )
        
        assert isinstance(results, list)
    
    def test_chat(self, manager):
        """Testa chat com RAG"""
        response = manager.chat(
            query="Quantos containers foram movimentados?",
            model="gpt-4-turbo",
            temperature=0.7,
            max_tokens=500
        )
        
        assert isinstance(response, str)
        # Resposta pode ser erro se serviços não estiverem disponíveis
    
    def test_get_stats(self, manager):
        """Testa obtenção de estatísticas"""
        stats = manager.get_stats()
        
        assert isinstance(stats, dict)
    
    def test_get_mime_type(self, manager):
        """Testa detecção de MIME type"""
        assert manager._get_mime_type(Path('test.pdf')) == 'application/pdf'
        assert manager._get_mime_type(Path('test.docx')) == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        assert manager._get_mime_type(Path('test.xlsx')) == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert manager._get_mime_type(Path('test.csv')) == 'text/csv'
        assert manager._get_mime_type(Path('test.txt')) == 'text/plain'


class TestHybridLLMManager:
    """Testes para HybridLLMManager"""
    
    @pytest.fixture
    def hybrid_manager(self):
        """Fixture para criar hybrid manager"""
        return HybridLLMManager()
    
    @pytest.fixture
    def sample_dataframe(self):
        """Fixture com DataFrame de exemplo"""
        return pd.DataFrame({
            'cliente': ['MICHELIN', 'GOODYEAR'],
            'qtd_container': [100, 50],
            'ano_mes': ['202503', '202503']
        })
    
    def test_initialization(self, hybrid_manager):
        """Testa inicialização do gerenciador híbrido"""
        assert hybrid_manager is not None
        assert hasattr(hybrid_manager, 'use_openrag')
        assert isinstance(hybrid_manager.use_openrag, bool)
    
    def test_generate_enhanced_response(self, hybrid_manager, sample_dataframe):
        """Testa geração de resposta"""
        response = hybrid_manager.generate_enhanced_response(
            query="Quantos containers a Michelin movimentou?",
            df=sample_dataframe,
            max_tokens=500
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_update_knowledge_base(self, hybrid_manager, sample_dataframe):
        """Testa atualização da base de conhecimento"""
        # Não deve lançar exceção
        hybrid_manager.update_knowledge_base(sample_dataframe)
    
    def test_reset_knowledge_base(self, hybrid_manager):
        """Testa reset da base de conhecimento"""
        # Não deve lançar exceção
        hybrid_manager.reset_knowledge_base()


class TestIntegrationScenarios:
    """Testes de cenários de integração completos"""
    
    @pytest.fixture
    def manager(self):
        """Fixture para criar manager"""
        return OpenRAGManager()
    
    @pytest.fixture
    def sample_data(self):
        """Fixture com dados de exemplo mais completos"""
        return pd.DataFrame({
            'cliente': ['MICHELIN', 'GOODYEAR', 'PIRELLI', 'MICHELIN', 'GOODYEAR'],
            'qtd_container': [100, 50, 75, 120, 60],
            'ano_mes': ['202501', '202501', '202501', '202502', '202502'],
            'porto': ['SANTOS', 'PARANAGUA', 'SANTOS', 'SANTOS', 'PARANAGUA'],
            'tipo_carga': ['PNEUS', 'PNEUS', 'PNEUS', 'PNEUS', 'PNEUS']
        })
    
    def test_full_workflow(self, manager, sample_data):
        """Testa workflow completo: ingestão -> busca -> chat"""
        # 1. Verificar saúde
        health = manager.health_check()
        if not health['overall']:
            pytest.skip("OpenRAG não disponível")
        
        # 2. Ingerir dados
        ingest_result = manager.ingest_dataframe(
            sample_data,
            metadata={'source': 'integration_test'}
        )
        
        if not ingest_result['success']:
            pytest.skip("Ingestão falhou - serviços podem não estar disponíveis")
        
        assert ingest_result['documents_indexed'] > 0
        
        # 3. Buscar
        search_results = manager.search(
            query="containers Michelin",
            filters={'cliente': 'MICHELIN'},
            top_k=5
        )
        
        assert isinstance(search_results, list)
        
        # 4. Chat
        chat_response = manager.chat(
            query="Quantos containers a Michelin movimentou no total?",
            context_filters={'cliente': 'MICHELIN'}
        )
        
        assert isinstance(chat_response, str)
        assert len(chat_response) > 0


class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    @pytest.fixture
    def manager(self):
        """Fixture para criar manager"""
        return OpenRAGManager()
    
    def test_invalid_dataframe(self, manager):
        """Testa ingestão com DataFrame inválido"""
        result = manager.ingest_dataframe(None)
        assert result['success'] == False
    
    def test_search_empty_query(self, manager):
        """Testa busca com query vazia"""
        results = manager.search(query="", top_k=5)
        assert isinstance(results, list)
    
    def test_chat_empty_query(self, manager):
        """Testa chat com query vazia"""
        response = manager.chat(query="")
        assert isinstance(response, str)


class TestPerformance:
    """Testes de performance"""
    
    @pytest.fixture
    def manager(self):
        """Fixture para criar manager"""
        return OpenRAGManager()
    
    @pytest.fixture
    def large_dataframe(self):
        """Fixture com DataFrame grande"""
        import numpy as np
        
        n_rows = 1000
        return pd.DataFrame({
            'cliente': np.random.choice(['MICHELIN', 'GOODYEAR', 'PIRELLI'], n_rows),
            'qtd_container': np.random.randint(10, 200, n_rows),
            'ano_mes': np.random.choice(['202501', '202502', '202503'], n_rows),
            'porto': np.random.choice(['SANTOS', 'PARANAGUA', 'RIO'], n_rows)
        })
    
    def test_large_dataframe_ingestion(self, manager, large_dataframe):
        """Testa ingestão de DataFrame grande"""
        import time
        
        start_time = time.time()
        result = manager.ingest_dataframe(
            large_dataframe,
            metadata={'source': 'performance_test'}
        )
        elapsed_time = time.time() - start_time
        
        if result['success']:
            # Deve processar 1000 registros em menos de 60 segundos
            assert elapsed_time < 60
            assert result['documents_indexed'] > 0
    
    def test_search_performance(self, manager):
        """Testa performance de busca"""
        import time
        
        start_time = time.time()
        results = manager.search(query="containers", top_k=10)
        elapsed_time = time.time() - start_time
        
        # Busca deve ser rápida (< 1 segundo)
        assert elapsed_time < 1.0


def test_environment_variables():
    """Testa se variáveis de ambiente estão configuradas"""
    # Variáveis opcionais
    openrag_enabled = os.getenv('USE_OPENRAG', 'false')
    assert openrag_enabled in ['true', 'false']
    
    # Se OpenRAG estiver habilitado, verificar outras variáveis
    if openrag_enabled == 'true':
        assert os.getenv('OPENRAG_API_URL') is not None
        assert os.getenv('OPENSEARCH_URL') is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

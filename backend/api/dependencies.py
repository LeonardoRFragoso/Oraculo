"""
Dependências para injeção
"""

from functools import lru_cache
import sys
from pathlib import Path

# Adicionar diretório pai ao path para importar módulos do backend
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from .llm_service import SimpleLLMService
from .config import settings

try:
    from src.data_ingestion import DataIngestionManager
except ImportError:
    DataIngestionManager = None


@lru_cache()
def get_llm_manager():
    """
    Obter instância do LLM Manager
    
    Usa cache para reutilizar a mesma instância
    """
    return SimpleLLMService()


@lru_cache()
def get_data_ingestion_manager():
    """
    Obter instância do Data Ingestion Manager
    """
    if DataIngestionManager is None:
        raise ImportError("DataIngestionManager não disponível")
    return DataIngestionManager()


def get_current_user():
    """
    Obter usuário atual (placeholder)
    
    TODO: Implementar autenticação real
    """
    return {"id": "user-123", "username": "demo"}

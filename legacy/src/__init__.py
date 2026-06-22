"""
Inicialização do pacote src
"""
from .data_processing import normalize_text, limpar_qtd_coluna, processar_dados, unificar_contagem_containers
from .query_interpreter import interpretar_pergunta
from .filters import aplicar_filtros
from .context_builder import construir_contexto
from .api_response import responder_pergunta
from .data_loader import carregar_planilhas, carregar_clientes

__all__ = [
    'normalize_text',
    'limpar_qtd_coluna',
    'processar_dados',
    'unificar_contagem_containers',
    'interpretar_pergunta',
    'aplicar_filtros',
    'construir_contexto',
    'responder_pergunta',
    'carregar_planilhas',
    'carregar_clientes'
]

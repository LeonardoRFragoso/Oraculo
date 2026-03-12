"""
Módulo de integração com OpenRAG para GPTRACKER
Substitui a implementação manual de RAG (FAISS + Sentence Transformers)
"""
import os
import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import requests
import json

logger = logging.getLogger(__name__)


class OpenRAGManager:
    """
    Gerenciador de integração com OpenRAG
    Fornece interface unificada para ingestão, busca e chat
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        opensearch_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Inicializa o gerenciador OpenRAG
        
        Args:
            api_url: URL da API do Langflow (default: http://localhost:7860)
            opensearch_url: URL do OpenSearch (default: http://localhost:9200)
            api_key: Chave de API para autenticação
        """
        self.api_url = api_url or os.getenv('OPENRAG_API_URL', 'http://localhost:7860')
        self.opensearch_url = opensearch_url or os.getenv('OPENSEARCH_URL', 'http://localhost:9200')
        self.api_key = api_key or os.getenv('OPENRAG_API_KEY', '')
        
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
        
        self.index_name = os.getenv('OPENRAG_INDEX_NAME', 'gptracker_knowledge')
        
        logger.info(f"OpenRAG Manager inicializado - API: {self.api_url}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saúde dos serviços OpenRAG
        
        Returns:
            Dict com status de cada serviço
        """
        health = {
            'langflow': False,
            'opensearch': False,
            'overall': False
        }
        
        try:
            # Verificar Langflow
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            health['langflow'] = response.status_code == 200
        except Exception as e:
            logger.warning(f"Langflow não disponível: {e}")
        
        try:
            # Verificar OpenSearch
            response = requests.get(f"{self.opensearch_url}/_cluster/health", timeout=5)
            health['opensearch'] = response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenSearch não disponível: {e}")
        
        health['overall'] = health['langflow'] and health['opensearch']
        return health
    
    def ingest_dataframe(
        self,
        df: pd.DataFrame,
        metadata: Optional[Dict] = None,
        chunk_strategy: str = 'semantic'
    ) -> Dict[str, Any]:
        """
        Ingere DataFrame no OpenRAG com chunking inteligente
        
        Args:
            df: DataFrame com dados a serem indexados
            metadata: Metadados adicionais para os documentos
            chunk_strategy: Estratégia de chunking ('semantic', 'fixed', 'auto')
        
        Returns:
            Dict com resultado da ingestão
        """
        if df.empty:
            return {'success': False, 'error': 'DataFrame vazio'}
        
        try:
            # Converter DataFrame para documentos estruturados
            documents = self._df_to_documents(df, metadata or {})
            
            # Enviar para OpenRAG via API
            response = self.session.post(
                f"{self.api_url}/api/v1/ingest",
                json={
                    'documents': documents,
                    'index_name': self.index_name,
                    'chunk_strategy': chunk_strategy,
                    'metadata': metadata
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Ingestão bem-sucedida: {result.get('documents_indexed', 0)} documentos")
                return {
                    'success': True,
                    'documents_indexed': result.get('documents_indexed', 0),
                    'chunks_created': result.get('chunks_created', 0)
                }
            else:
                logger.error(f"Erro na ingestão: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            logger.error(f"Erro ao ingerir DataFrame: {e}")
            return {'success': False, 'error': str(e)}
    
    def _df_to_documents(self, df: pd.DataFrame, metadata: Dict) -> List[Dict]:
        """
        Converte DataFrame em lista de documentos estruturados
        
        Args:
            df: DataFrame fonte
            metadata: Metadados base
        
        Returns:
            Lista de documentos no formato OpenRAG
        """
        documents = []
        
        # Detectar colunas importantes
        client_cols = [col for col in df.columns if any(k in col.lower() for k in ['cliente', 'consignatario', 'importador', 'exportador'])]
        quantity_cols = [col for col in df.columns if any(k in col.lower() for k in ['qtd', 'quantidade', 'container', 'teus'])]
        date_cols = [col for col in df.columns if any(k in col.lower() for k in ['data', 'mes', 'ano', 'periodo'])]
        
        # Criar documentos por registro
        for idx, row in df.iterrows():
            content_parts = []
            doc_metadata = metadata.copy()
            
            # Construir conteúdo textual
            for col, value in row.items():
                if pd.notna(value):
                    content_parts.append(f"{col}: {value}")
                    
                    # Adicionar campos importantes aos metadados
                    if col in client_cols:
                        doc_metadata['cliente'] = str(value)
                    elif col in quantity_cols:
                        doc_metadata['quantidade'] = float(value) if isinstance(value, (int, float)) else value
                    elif col in date_cols:
                        doc_metadata['periodo'] = str(value)
            
            # Adicionar índice do registro
            doc_metadata['record_index'] = int(idx)
            doc_metadata['source_type'] = 'dataframe'
            doc_metadata['ingestion_timestamp'] = datetime.now().isoformat()
            
            documents.append({
                'content': ' | '.join(content_parts),
                'metadata': doc_metadata
            })
        
        # Criar também documentos agregados (resumos)
        if client_cols and quantity_cols:
            try:
                client_col = client_cols[0]
                qty_col = quantity_cols[0]
                
                # Converter quantidade para numérico
                df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce')
                
                # Agrupar por cliente
                summary = df.groupby(client_col).agg({
                    qty_col: ['sum', 'count', 'mean']
                }).reset_index()
                
                for _, row in summary.iterrows():
                    cliente = row[client_col]
                    total = row[(qty_col, 'sum')]
                    count = row[(qty_col, 'count')]
                    media = row[(qty_col, 'mean')]
                    
                    documents.append({
                        'content': f"Resumo do cliente {cliente}: Total de {total:.0f} unidades em {count} operações, média de {media:.2f} por operação",
                        'metadata': {
                            **metadata,
                            'tipo': 'resumo_cliente',
                            'cliente': str(cliente),
                            'total': float(total),
                            'operacoes': int(count),
                            'media': float(media)
                        }
                    })
            except Exception as e:
                logger.warning(f"Erro ao criar resumos: {e}")
        
        return documents
    
    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        top_k: int = 5,
        rerank: bool = True,
        hybrid: bool = True
    ) -> List[Dict]:
        """
        Busca semântica com filtros e reranking
        
        Args:
            query: Consulta em linguagem natural
            filters: Filtros de metadados (ex: {'cliente': 'MICHELIN'})
            top_k: Número de resultados a retornar
            rerank: Aplicar reranking nos resultados
            hybrid: Usar busca híbrida (vetorial + keyword)
        
        Returns:
            Lista de documentos relevantes com scores
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/search",
                json={
                    'query': query,
                    'index_name': self.index_name,
                    'filters': filters or {},
                    'top_k': top_k,
                    'rerank': rerank,
                    'hybrid': hybrid
                },
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                logger.info(f"🔍 Busca retornou {len(results.get('documents', []))} resultados")
                return results.get('documents', [])
            else:
                logger.error(f"Erro na busca: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Erro ao buscar: {e}")
            return []
    
    def chat(
        self,
        query: str,
        context_filters: Optional[Dict] = None,
        model: str = "gpt-4-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Chat com RAG - gera resposta usando contexto recuperado
        
        Args:
            query: Pergunta do usuário
            context_filters: Filtros para recuperação de contexto
            model: Modelo LLM a usar
            temperature: Temperatura para geração
            max_tokens: Máximo de tokens na resposta
            conversation_id: ID da conversa para manter histórico
        
        Returns:
            Resposta gerada pelo LLM com contexto
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/chat",
                json={
                    'query': query,
                    'index_name': self.index_name,
                    'filters': context_filters or {},
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'conversation_id': conversation_id
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"💬 Chat respondeu com {len(result.get('response', ''))} caracteres")
                return result.get('response', '')
            else:
                logger.error(f"Erro no chat: {response.status_code}")
                return f"Erro ao gerar resposta: HTTP {response.status_code}"
        
        except Exception as e:
            logger.error(f"Erro no chat: {e}")
            return f"Erro ao gerar resposta: {str(e)}"
    
    def ingest_file(
        self,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Ingere arquivo diretamente (PDF, DOCX, Excel, CSV)
        Usa Docling para parsing automático
        
        Args:
            file_path: Caminho do arquivo
            metadata: Metadados adicionais
        
        Returns:
            Resultado da ingestão
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'success': False, 'error': 'Arquivo não encontrado'}
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, self._get_mime_type(file_path))}
                data = {
                    'index_name': self.index_name,
                    'metadata': json.dumps(metadata or {})
                }
                
                response = self.session.post(
                    f"{self.api_url}/api/v1/ingest/file",
                    files=files,
                    data=data,
                    timeout=300
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Arquivo ingerido: {file_path.name}")
                return {
                    'success': True,
                    'file': file_path.name,
                    'documents_indexed': result.get('documents_indexed', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            logger.error(f"Erro ao ingerir arquivo: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Retorna MIME type baseado na extensão"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
            '.txt': 'text/plain',
            '.json': 'application/json'
        }
        return mime_types.get(file_path.suffix.lower(), 'application/octet-stream')
    
    def delete_index(self) -> Dict[str, Any]:
        """
        Deleta o índice atual (útil para reset)
        
        Returns:
            Resultado da operação
        """
        try:
            response = self.session.delete(
                f"{self.api_url}/api/v1/index/{self.index_name}",
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"🗑️ Índice {self.index_name} deletado")
                return {'success': True}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Erro ao deletar índice: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do índice
        
        Returns:
            Estatísticas (documentos, chunks, tamanho, etc)
        """
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/index/{self.index_name}/stats",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f"HTTP {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Erro ao obter stats: {e}")
            return {'error': str(e)}


class HybridLLMManager:
    """
    Gerenciador híbrido que suporta tanto OpenRAG quanto o sistema legado
    Permite migração gradual sem quebrar funcionalidades existentes
    """
    
    def __init__(self):
        """Inicializa gerenciador híbrido"""
        self.use_openrag = os.getenv('USE_OPENRAG', 'false').lower() == 'true'
        
        if self.use_openrag:
            self.openrag_manager = OpenRAGManager()
            
            # Verificar se OpenRAG está disponível
            health = self.openrag_manager.health_check()
            if not health['overall']:
                logger.warning("⚠️ OpenRAG não disponível, usando sistema legado")
                self.use_openrag = False
        
        if not self.use_openrag:
            # Importar sistema legado apenas se necessário
            from .advanced_llm import AdvancedLLMManager
            self.legacy_manager = AdvancedLLMManager()
            logger.info("📦 Usando sistema legado (FAISS)")
        else:
            logger.info("🚀 Usando OpenRAG")
    
    def generate_enhanced_response(
        self,
        query: str,
        df: pd.DataFrame,
        max_tokens: int = 1000
    ) -> str:
        """
        Gera resposta usando OpenRAG ou sistema legado
        Interface compatível com AdvancedLLMManager
        """
        if self.use_openrag:
            # Usar OpenRAG
            return self.openrag_manager.chat(
                query=query,
                model="gpt-4-turbo",
                max_tokens=max_tokens
            )
        else:
            # Usar sistema legado
            return self.legacy_manager.generate_enhanced_response(
                query=query,
                df=df,
                max_tokens=max_tokens
            )
    
    def update_knowledge_base(self, df: pd.DataFrame):
        """
        Atualiza base de conhecimento
        Interface compatível com AdvancedLLMManager
        """
        if self.use_openrag:
            # Ingerir no OpenRAG
            result = self.openrag_manager.ingest_dataframe(
                df,
                metadata={'source': 'gptracker_update'}
            )
            logger.info(f"Base atualizada: {result}")
        else:
            # Usar sistema legado
            self.legacy_manager.create_knowledge_base_from_data(df)
    
    def reset_knowledge_base(self):
        """
        Reseta base de conhecimento
        Interface compatível com AdvancedLLMManager
        """
        if self.use_openrag:
            result = self.openrag_manager.delete_index()
            logger.info(f"Base resetada: {result}")
        else:
            # Resetar sistema legado
            import os
            if os.path.exists('vector_index.faiss'):
                os.remove('vector_index.faiss')
            if os.path.exists('documents.pkl'):
                os.remove('documents.pkl')
            logger.info("Base legado resetada")

"""
Serviço RAG - Retrieval-Augmented Generation
Sistema de busca semântica em documentos usando embeddings
"""

import os
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

logger = logging.getLogger(__name__)


class RAGService:
    """Serviço de RAG para busca semântica em documentos"""
    
    def __init__(self, storage_dir: str = "../dados/rag_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivos de persistência
        self.index_file = self.storage_dir / "faiss_index.bin"
        self.documents_file = self.storage_dir / "documents.pkl"
        self.metadata_file = self.storage_dir / "metadata.pkl"
        
        # Modelo de embeddings
        logger.info("Carregando modelo de embeddings...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimensão do modelo all-MiniLM-L6-v2
        
        # Vector store (FAISS)
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Carregar índice existente
        self._load_index()
    
    def _load_index(self):
        """Carrega índice FAISS e documentos do disco"""
        try:
            if self.index_file.exists() and self.documents_file.exists():
                logger.info("Carregando índice existente...")
                self.index = faiss.read_index(str(self.index_file))
                
                with open(self.documents_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                logger.info(f"✓ Índice carregado: {len(self.documents)} documentos")
            else:
                logger.info("Criando novo índice FAISS...")
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.documents = []
                self.metadata = []
        except Exception as e:
            logger.error(f"Erro ao carregar índice: {e}")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.documents = []
            self.metadata = []
    
    def _save_index(self):
        """Salva índice FAISS e documentos no disco"""
        try:
            faiss.write_index(self.index, str(self.index_file))
            
            with open(self.documents_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"✓ Índice salvo: {len(self.documents)} documentos")
        except Exception as e:
            logger.error(f"Erro ao salvar índice: {e}")
    
    def add_document(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000
    ) -> int:
        """
        Adiciona documento ao índice
        
        Args:
            content: Conteúdo do documento
            metadata: Metadados (filename, type, etc.)
            chunk_size: Tamanho dos chunks em caracteres
            
        Returns:
            Número de chunks adicionados
        """
        if not content or not content.strip():
            logger.warning("Conteúdo vazio, ignorando")
            return 0
        
        # Dividir em chunks
        chunks = self._chunk_text(content, chunk_size)
        logger.info(f"Documento dividido em {len(chunks)} chunks")
        
        # Gerar embeddings
        embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        embeddings = np.array(embeddings).astype('float32')
        
        # Adicionar ao índice FAISS
        self.index.add(embeddings)
        
        # Armazenar documentos e metadados
        for i, chunk in enumerate(chunks):
            self.documents.append(chunk)
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['chunk_id'] = i
            chunk_metadata['total_chunks'] = len(chunks)
            self.metadata.append(chunk_metadata)
        
        # Salvar
        self._save_index()
        
        return len(chunks)
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        Divide texto em chunks menores
        
        Args:
            text: Texto para dividir
            chunk_size: Tamanho aproximado de cada chunk
            
        Returns:
            Lista de chunks
        """
        # Dividir por parágrafos primeiro
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            if current_size + para_size > chunk_size and current_chunk:
                # Salvar chunk atual
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Adicionar último chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos relevantes
        
        Args:
            query: Consulta de busca
            top_k: Número de resultados
            min_score: Score mínimo (distância L2)
            
        Returns:
            Lista de documentos com scores
        """
        if not self.documents:
            logger.warning("Índice vazio, nenhum documento para buscar")
            return []
        
        # Gerar embedding da query
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        # Buscar no FAISS
        k = min(top_k, len(self.documents))
        distances, indices = self.index.search(query_embedding, k)
        
        # Formatar resultados
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):  # Validar índice
                results.append({
                    'content': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(dist),
                    'similarity': 1.0 / (1.0 + float(dist))  # Converter distância em similaridade
                })
        
        # Filtrar por score mínimo
        results = [r for r in results if r['score'] <= min_score or min_score == 0.0]
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do índice"""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'embedding_dim': self.embedding_dim,
            'storage_dir': str(self.storage_dir)
        }
    
    def clear_index(self):
        """Limpa todo o índice"""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.documents = []
        self.metadata = []
        self._save_index()
        logger.info("✓ Índice limpo")

"""
Sprint 4 — Per-source Vector Store

Stores one FAISS index per data source (namespace isolation).
Embedding backends (in order of preference):
  1. OpenAI text-embedding-3-small  (best quality, requires API key)
  2. TF-IDF + cosine similarity      (zero API cost, works offline)

Each source gets its own directory under storage_root/source_id/:
    faiss_index.bin
    chunks.pkl
    metadata.pkl
    tfidf_matrix.pkl   (if TF-IDF backend)
"""

import logging
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_OPENAI_DIM = 1536   # text-embedding-3-small
_TFIDF_DIM  = 512    # reduced via TruncatedSVD (LSA)


@dataclass
class SearchResult:
    content: str
    source_id: str
    score: float          # 0-1 similarity (higher = better)
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0


class VectorStore:
    """
    Per-source vector store with automatic backend selection.

    Usage:
        store = VectorStore()
        store.add_texts("src-123", ["text chunk 1", "text chunk 2"], [{}, {}])
        results = store.search("src-123", "quarterly revenue", top_k=5)
    """

    def __init__(self, storage_root: str = "../dados/vector_store"):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._backend = self._detect_backend()
        self._openai_client = None
        self._source_dims: Dict[str, int] = {}
        logger.info(f"VectorStore initialized — backend: {self._backend}")

    def _detect_backend(self) -> str:
        if os.getenv("OPENAI_API_KEY", "").startswith("sk-"):
            return "openai"
        return "tfidf"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_texts(
        self,
        source_id: str,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Index a list of text chunks for a source. Returns chunk count."""
        if not texts:
            return 0
        metadatas = metadatas or [{} for _ in texts]

        logger.info(f"Indexing {len(texts)} chunks for source {source_id[:8]}... (backend={self._backend})")

        embeddings = self._embed(texts, source_id)
        self._save_index(source_id, texts, metadatas, embeddings)
        logger.info(f"✓ Indexed {len(texts)} chunks → {source_id[:8]}")
        return len(texts)

    def search(
        self,
        source_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Search a source's index for relevant chunks."""
        store_dir = self._source_dir(source_id)
        if not store_dir.exists():
            return []

        chunks, metadata = self._load_chunks(source_id)
        if not chunks:
            return []

        if self._backend == "openai":
            return self._search_faiss(source_id, query, chunks, metadata, top_k)
        return self._search_tfidf(source_id, query, chunks, metadata, top_k)

    def search_many(
        self,
        source_ids: List[str],
        query: str,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Search across multiple sources, returns top_k merged results."""
        all_results = []
        for sid in source_ids:
            results = self.search(sid, query, top_k=top_k)
            all_results.extend(results)
        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:top_k]

    def delete_source(self, source_id: str) -> bool:
        """Remove all indexed data for a source."""
        import shutil
        store_dir = self._source_dir(source_id)
        if store_dir.exists():
            shutil.rmtree(store_dir)
            logger.info(f"Deleted vector store for {source_id[:8]}")
            return True
        return False

    def has_index(self, source_id: str) -> bool:
        return self._source_dir(source_id).exists()

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def _embed(self, texts: List[str], source_id: str) -> np.ndarray:
        if self._backend == "openai":
            return self._embed_openai(texts, source_id)
        return self._embed_tfidf(texts, source_id)

    def _embed_openai(self, texts: List[str], source_id: str) -> np.ndarray:
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = self._openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        arr = np.array([item.embedding for item in resp.data], dtype="float32")
        self._source_dims[source_id] = arr.shape[1]
        return arr

    def _embed_tfidf(self, texts: List[str], source_id: str) -> np.ndarray:
        """
        TF-IDF + LSA (Latent Semantic Analysis) embeddings.
        Completely offline — no API cost.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        from sklearn.preprocessing import normalize

        n_components = min(_TFIDF_DIM, len(texts) - 1) if len(texts) > 1 else 1

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=8000,
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)

        if n_components < tfidf_matrix.shape[1] and n_components >= 1:
            svd = TruncatedSVD(n_components=n_components, random_state=42)
            embeddings = svd.fit_transform(tfidf_matrix)
        else:
            embeddings = tfidf_matrix.toarray()

        embeddings = normalize(embeddings, norm="l2").astype("float32")

        # Save vectorizer + svd for query embedding later
        store_dir = self._source_dir(source_id)
        store_dir.mkdir(parents=True, exist_ok=True)
        with open(store_dir / "tfidf_vectorizer.pkl", "wb") as f:
            pickle.dump(vectorizer, f)
        if n_components < tfidf_matrix.shape[1] and n_components >= 1:
            with open(store_dir / "tfidf_svd.pkl", "wb") as f:
                pickle.dump(svd, f)

        self._source_dims[source_id] = embeddings.shape[1]
        return embeddings

    def _embed_query_tfidf(self, source_id: str, query: str) -> np.ndarray:
        from sklearn.preprocessing import normalize
        store_dir = self._source_dir(source_id)
        with open(store_dir / "tfidf_vectorizer.pkl", "rb") as f:
            vectorizer = pickle.load(f)
        vec = vectorizer.transform([query])
        svd_path = store_dir / "tfidf_svd.pkl"
        if svd_path.exists():
            with open(svd_path, "rb") as f:
                svd = pickle.load(f)
            vec = svd.transform(vec)
        else:
            vec = vec.toarray()
        return normalize(vec.astype("float32"), norm="l2")

    # ------------------------------------------------------------------
    # FAISS index
    # ------------------------------------------------------------------

    def _save_index(
        self,
        source_id: str,
        chunks: List[str],
        metadata: List[Dict],
        embeddings: np.ndarray,
    ):
        import faiss
        store_dir = self._source_dir(source_id)
        store_dir.mkdir(parents=True, exist_ok=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)   # Inner product = cosine on normalized vecs
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        faiss.write_index(index, str(store_dir / "faiss_index.bin"))
        with open(store_dir / "chunks.pkl", "wb") as f:
            pickle.dump(chunks, f)
        with open(store_dir / "metadata.pkl", "wb") as f:
            pickle.dump(metadata, f)

    def _load_chunks(self, source_id: str) -> Tuple[List[str], List[Dict]]:
        store_dir = self._source_dir(source_id)
        try:
            with open(store_dir / "chunks.pkl", "rb") as f:
                chunks = pickle.load(f)
            with open(store_dir / "metadata.pkl", "rb") as f:
                metadata = pickle.load(f)
            return chunks, metadata
        except Exception:
            return [], []

    def _search_faiss(
        self,
        source_id: str,
        query: str,
        chunks: List[str],
        metadata: List[Dict],
        top_k: int,
    ) -> List[SearchResult]:
        import faiss
        store_dir = self._source_dir(source_id)
        index = faiss.read_index(str(store_dir / "faiss_index.bin"))

        if self._backend == "openai":
            q_emb = self._embed_openai([query], source_id)
        else:
            q_emb = self._embed_query_tfidf(source_id, query)

        faiss.normalize_L2(q_emb)
        k = min(top_k, len(chunks))
        scores, indices = index.search(q_emb, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(chunks):
                results.append(SearchResult(
                    content=chunks[idx],
                    source_id=source_id,
                    score=float(score),
                    metadata=metadata[idx],
                    chunk_index=int(idx),
                ))
        return results

    def _search_tfidf(
        self,
        source_id: str,
        query: str,
        chunks: List[str],
        metadata: List[Dict],
        top_k: int,
    ) -> List[SearchResult]:
        return self._search_faiss(source_id, query, chunks, metadata, top_k)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _source_dir(self, source_id: str) -> Path:
        return self.storage_root / source_id

"""
Sprint 4 — Document Indexer

Automatically indexes document sources into the VectorStore
when they are connected via SchemaDiscovery.

Handles:
  - PDF, DOCX, TXT, XML  via DocumentConnector
  - Chunking with configurable overlap
  - Metadata enrichment (page, source_name, domain)
  - Re-indexing on demand
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

_DOCUMENT_TYPES = {"pdf", "docx", "txt", "xml"}


@dataclass
class IndexingResult:
    source_id: str
    success: bool
    chunks_indexed: int = 0
    error: Optional[str] = None


class DocumentIndexer:
    """
    Indexes document sources into the per-source VectorStore.

    Usage:
        indexer = DocumentIndexer()
        result = indexer.index(source_id="abc-123", record=registry_record)
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ):
        self.vector_store = vector_store or VectorStore()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def index(self, source_id: str, record: Any) -> IndexingResult:
        """
        Index a document source. Called automatically during /connect.

        Args:
            source_id: Registry ID.
            record: DataSourceRecord from registry.
        """
        if record.connector_type not in _DOCUMENT_TYPES:
            return IndexingResult(
                source_id=source_id,
                success=False,
                error=f"Not a document source: {record.connector_type}",
            )

        logger.info(f"Indexing document source: {record.name} ({record.connector_type})")

        try:
            import sys
            _root = str(Path(__file__).parent.parent)
            if _root not in sys.path:
                sys.path.insert(0, _root)
            from connectors.files import DocumentConnector

            connector = DocumentConnector(record.config)
            if not connector.connect():
                return IndexingResult(
                    source_id=source_id,
                    success=False,
                    error="Could not connect to document source",
                )

            result = connector.extract()
            connector.close()

            if not result.success or not result.raw_text:
                return IndexingResult(
                    source_id=source_id,
                    success=False,
                    error=result.error or "No text extracted from document",
                )

            # Chunk the text
            chunks = self._chunk_text(result.raw_text)
            if not chunks:
                return IndexingResult(
                    source_id=source_id,
                    success=False,
                    error="Document produced no indexable chunks",
                )

            # Build per-chunk metadata
            metadatas = [
                {
                    "source_id": source_id,
                    "source_name": record.name,
                    "connector_type": record.connector_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "file_path": record.config.get("path", ""),
                }
                for i in range(len(chunks))
            ]

            # Delete stale index and re-index
            self.vector_store.delete_source(source_id)
            count = self.vector_store.add_texts(source_id, chunks, metadatas)

            logger.info(
                f"✓ Indexed {count} chunks from '{record.name}'"
            )
            return IndexingResult(
                source_id=source_id,
                success=True,
                chunks_indexed=count,
            )

        except Exception as e:
            logger.error(f"Document indexing error for {source_id}: {e}", exc_info=True)
            return IndexingResult(source_id=source_id, success=False, error=str(e))

    def index_text(
        self,
        source_id: str,
        text: str,
        source_name: str = "text",
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> IndexingResult:
        """Index raw text directly (useful for tabular dataset summaries)."""
        chunks = self._chunk_text(text)
        if not chunks:
            return IndexingResult(source_id=source_id, success=False, error="Empty text")

        base_meta = {"source_id": source_id, "source_name": source_name}
        if extra_metadata:
            base_meta.update(extra_metadata)
        metadatas = [
            {**base_meta, "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]
        count = self.vector_store.add_texts(source_id, chunks, metadatas)
        return IndexingResult(source_id=source_id, success=True, chunks_indexed=count)

    # ------------------------------------------------------------------
    # Text chunking
    # ------------------------------------------------------------------

    def _chunk_text(self, text: str) -> List[str]:
        """
        Chunk text with overlap using sentence-aware boundaries.
        Prefers splitting at paragraph/sentence boundaries.
        """
        if not text or not text.strip():
            return []

        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        # Split into paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks: List[str] = []
        current_chars: List[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)

            # Paragraph alone exceeds chunk_size — split at sentences
            if para_len > self.chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sent in sentences:
                    if current_len + len(sent) > self.chunk_size and current_chars:
                        chunks.append(" ".join(current_chars))
                        # Keep overlap
                        overlap_text = " ".join(current_chars)[-self.chunk_overlap:]
                        current_chars = [overlap_text, sent] if overlap_text else [sent]
                        current_len = len(overlap_text) + len(sent)
                    else:
                        current_chars.append(sent)
                        current_len += len(sent)
            elif current_len + para_len > self.chunk_size and current_chars:
                chunks.append("\n\n".join(current_chars))
                # Keep overlap
                overlap_text = "\n\n".join(current_chars)[-self.chunk_overlap:]
                current_chars = [overlap_text, para] if overlap_text else [para]
                current_len = len(overlap_text) + para_len
            else:
                current_chars.append(para)
                current_len += para_len

        if current_chars:
            chunks.append("\n\n".join(current_chars))

        return [c for c in chunks if len(c.strip()) > 20]

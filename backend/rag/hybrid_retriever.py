"""
Sprint 4 — Hybrid Retriever

Fuses structured (SQL) and unstructured (document) results
into a single coherent natural language answer.

Flow:
    question
      ├─ [structured sources] → NL2SQL → SQL results (rows + columns)
      ├─ [document sources]   → VectorSearch → relevant chunks
      └─ LLM Synthesis → fused natural language answer
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rag.vector_store import SearchResult, VectorStore

logger = logging.getLogger(__name__)


@dataclass
class HybridResult:
    question: str
    answer: str
    sql_results: Optional[Dict[str, Any]] = None    # ExecutionResult dict
    doc_chunks: List[SearchResult] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)
    sql_query: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "sql_results": self.sql_results,
            "doc_chunks": [
                {
                    "content": r.content[:500],
                    "source_id": r.source_id,
                    "score": round(r.score, 4),
                    "metadata": r.metadata,
                }
                for r in self.doc_chunks
            ],
            "sources_used": self.sources_used,
            "sql_query": self.sql_query,
            "error": self.error,
        }


_SYNTHESIS_SYSTEM = """You are Oráculo AI, a corporate intelligence analyst.
Your job is to answer business questions by combining:
  1. Structured data results (SQL query results from databases/spreadsheets)
  2. Relevant document excerpts (contracts, reports, PDFs, etc.)

Rules:
- Write a clear, concise business answer in the same language as the question.
- Cite data numbers precisely when available (e.g. "Michelin had R$ 32,000 in revenue").
- When document context is available, reference it to enrich the answer.
- If data contradicts documents, note the discrepancy.
- Keep the answer focused — no more than 3-4 sentences unless detail is needed.
- Never invent numbers not present in the provided context.
"""


class HybridRetriever:
    """
    Retrieves and synthesizes answers from both structured and
    unstructured data sources.

    Usage:
        retriever = HybridRetriever()
        result = await retriever.retrieve(
            question="Qual é a receita da Michelin e quais são os termos do contrato?",
            structured_sources=[record1, ...],
            document_sources=[record2, ...],
        )
        print(result.answer)
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        top_k_docs: int = 4,
    ):
        self.vector_store = vector_store or VectorStore()
        self.top_k_docs = top_k_docs
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            import sys
            from pathlib import Path
            _root = str(Path(__file__).parent.parent)
            if _root not in sys.path:
                sys.path.insert(0, _root)
            from core.llm_client import LLMClient
            self._llm = LLMClient()
        return self._llm

    async def retrieve(
        self,
        question: str,
        structured_sources: Optional[List[Any]] = None,  # DataSourceRecord list
        document_sources: Optional[List[Any]] = None,    # DataSourceRecord list
    ) -> HybridResult:
        """
        Retrieve from all sources and synthesize a fused answer.
        """
        sql_results = None
        sql_query = None
        doc_chunks: List[SearchResult] = []
        sources_used = []
        errors = []

        # 1. NL2SQL on structured sources
        if structured_sources:
            sql_result_obj = await self._run_nl2sql(question, structured_sources)
            if sql_result_obj and sql_result_obj.get("success"):
                sql_results = sql_result_obj
                sql_query = sql_result_obj.get("sql")
                sources_used.extend(
                    s.id for s in structured_sources
                    if s.id in sql_result_obj.get("sources_used", [])
                )
            elif sql_result_obj and sql_result_obj.get("error"):
                errors.append(f"SQL: {sql_result_obj['error']}")

        # 2. Vector search on document sources
        if document_sources:
            doc_source_ids = [s.id for s in document_sources]
            indexed_ids = [sid for sid in doc_source_ids
                           if self.vector_store.has_index(sid)]
            if indexed_ids:
                doc_chunks = self.vector_store.search_many(
                    indexed_ids, question, top_k=self.top_k_docs
                )
                sources_used.extend(
                    set(r.source_id for r in doc_chunks)
                )
            else:
                errors.append("Document sources not yet indexed — reconnect to index them.")

        # 3. Synthesize
        if not sql_results and not doc_chunks:
            return HybridResult(
                question=question,
                answer="Não encontrei dados relevantes. Conecte uma fonte estruturada ou documento.",
                error="; ".join(errors) if errors else None,
            )

        answer = self._synthesize(question, sql_results, doc_chunks)

        return HybridResult(
            question=question,
            answer=answer,
            sql_results=sql_results,
            doc_chunks=doc_chunks,
            sources_used=list(set(sources_used)),
            sql_query=sql_query,
        )

    async def _run_nl2sql(
        self, question: str, sources: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """Run NL2SQL pipeline for the first available structured source."""
        if not sources:
            return None
        try:
            import sys
            from pathlib import Path
            _root = str(Path(__file__).parent.parent)
            if _root not in sys.path:
                sys.path.insert(0, _root)
            from api.routers.query import query_datasource, QueryRequest
            req = QueryRequest(question=question, explain=True)
            resp = await query_datasource(sources[0].id, req)
            return resp.dict()
        except Exception as e:
            logger.warning(f"NL2SQL in hybrid failed: {e}")
            return {"success": False, "error": str(e)}

    def _synthesize(
        self,
        question: str,
        sql_results: Optional[Dict[str, Any]],
        doc_chunks: List[SearchResult],
    ) -> str:
        """Use LLM to fuse SQL results and document excerpts into one answer."""
        parts = []

        if sql_results and sql_results.get("rows"):
            rows_preview = sql_results["rows"][:10]
            cols = sql_results.get("columns", [])
            parts.append("=== STRUCTURED DATA (SQL result) ===")
            if sql_results.get("sql"):
                parts.append(f"Query: {sql_results['sql']}")
            parts.append(f"Columns: {', '.join(cols)}")
            for row in rows_preview:
                parts.append(str(row))
            if sql_results.get("truncated"):
                parts.append(f"... (showing first 10 of {sql_results.get('row_count')} rows)")

        if doc_chunks:
            parts.append("\n=== DOCUMENT EXCERPTS ===")
            for i, chunk in enumerate(doc_chunks[:4], 1):
                source = chunk.metadata.get("source_name", chunk.source_id[:8])
                parts.append(f"[{i}] Source: {source} (relevance: {chunk.score:.2f})")
                parts.append(chunk.content[:600])
                parts.append("")

        if not parts:
            return "Nenhum dado encontrado para responder a pergunta."

        context = "\n".join(parts)
        user_prompt = (
            f"=== QUESTION ===\n{question}\n\n"
            f"=== AVAILABLE CONTEXT ===\n{context}\n\n"
            "Based on the context above, provide a concise business answer."
        )

        try:
            llm = self._get_llm()
            resp = llm.chat(
                system=_SYNTHESIS_SYSTEM,
                user=user_prompt,
                max_tokens=600,
                temperature=0.2,
                model=llm.smart_model,
            )
            return resp.content.strip()
        except Exception as e:
            logger.error(f"Synthesis LLM error: {e}")
            # Fallback: return the raw SQL explanation + top chunk
            fallback = []
            if sql_results and sql_results.get("sql_explanation"):
                fallback.append(sql_results["sql_explanation"])
            if doc_chunks:
                fallback.append(f"Documento relevante: {doc_chunks[0].content[:300]}")
            return " | ".join(fallback) if fallback else "Erro na síntese dos resultados."

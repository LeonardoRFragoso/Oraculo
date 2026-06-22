"""
Query Router — decides whether a question should be answered by:
  A) NL2SQL   → structured data question  ("Quais clientes compraram mais?")
  B) RAG      → document/unstructured question ("O que diz o contrato?")
  C) HYBRID   → both needed               ("Explique a queda de receita")
  D) DIRECT   → simple factual / greeting  ("Olá", "Quantas tabelas temos?")

Classification uses a fast keyword-based heuristic first, then
falls back to a lightweight LLM classifier for ambiguous cases.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    NL2SQL = "nl2sql"
    RAG = "rag"
    HYBRID = "hybrid"
    DIRECT = "direct"


@dataclass
class RouterDecision:
    query_type: QueryType
    confidence: float
    reason: str
    suggested_sources: List[str]   # source_ids to use


# ---------------------------------------------------------------------------
# Heuristic signal lists
# ---------------------------------------------------------------------------

_SQL_SIGNALS = [
    # Aggregation
    r"\b(total|soma|somar|sum|count|contar|quantos|quantas|media|média|average|máximo|maximo|mínimo|minimo|max|min)\b",
    # Ranking
    r"\b(mais|menos|maior|menor|melhor|pior|top|ranking|rank|primeiro|último)\b",
    r"\b(cresceu|caiu|aumentou|diminuiu|variação|variacao|diferença|diferenca|comparar|comparativo)\b",
    # Time filters
    r"\b(ano|mês|mes|semana|trimestre|ontem|hoje|2\d{3}|janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b",
    # Data retrieval
    r"\b(liste|listar|mostre|mostrar|quais|quem|quando|onde|como|por que|porque)\b",
    # Filtering
    r"\b(clientes?|produtos?|vendas?|pedidos?|faturas?|pagamentos?|receita|lucro|margem)\b",
]

_RAG_SIGNALS = [
    r"\b(contrato|cláusula|clausula|acordo|documento|relatório|relatorio|ata|policy|política|política|manual|procedimento|norma|regulamento)\b",
    r"\b(diz|descreve|fala|menciona|explica|define|trata|aborda|consta|prevê|preve)\b",
    r"\b(PDF|DOCX|TXT|texto|arquivo|documento)\b",
    r"\b(resumo|resume|resumir|síntese|sintese|extrair|extraia)\b",
]

_DIRECT_SIGNALS = [
    r"^(olá|ola|oi|tudo bem|bom dia|boa tarde|boa noite|hello|hi)\b",
    r"^(obrigad|thanks?|thank you)\b",
    r"\b(quantas tabelas|quantas fontes|fontes conectadas|fontes disponíveis|catalogo|catálogo)\b",
    r"\b(me ajude|o que você|o que voce|como funciona|o que é|o que é)\b",
]

_SQL_RES = [re.compile(p, re.IGNORECASE) for p in _SQL_SIGNALS]
_RAG_RES = [re.compile(p, re.IGNORECASE) for p in _RAG_SIGNALS]
_DIRECT_RES = [re.compile(p, re.IGNORECASE) for p in _DIRECT_SIGNALS]


class QueryRouter:
    """
    Routes a question to the right execution strategy.

    Usage:
        router = QueryRouter()
        decision = router.route(
            question="Quais clientes tiveram mais receita em 2025?",
            available_sources=[...],  # DataSourceRecord list
        )
        print(decision.query_type)    # QueryType.NL2SQL
    """

    def __init__(self, llm_fallback: bool = True):
        self._llm_fallback = llm_fallback

    def route(
        self,
        question: str,
        available_sources: Optional[List[Any]] = None,
    ) -> RouterDecision:
        """Classify the question and return a routing decision."""
        available_sources = available_sources or []

        # Gather connected source IDs
        db_sources = [
            s.id for s in available_sources
            if s.connector_type in ("sqlite", "postgresql", "mysql", "mongodb", "sqlserver")
        ]
        file_tabular = [
            s.id for s in available_sources
            if s.connector_type in ("csv", "excel", "parquet", "json")
               and any(d.get("column_count", 0) > 0 for d in s.datasets)
        ]
        doc_sources = [
            s.id for s in available_sources
            if s.connector_type in ("pdf", "docx", "txt", "xml")
        ]
        structured_sources = db_sources + file_tabular
        all_ids = [s.id for s in available_sources]

        # 1. Direct (greeting / catalog meta-question)
        if any(p.search(question) for p in _DIRECT_RES):
            return RouterDecision(
                query_type=QueryType.DIRECT,
                confidence=0.9,
                reason="Meta-question or greeting detected",
                suggested_sources=all_ids,
            )

        sql_score = sum(1 for p in _SQL_RES if p.search(question))
        rag_score = sum(1 for p in _RAG_RES if p.search(question))

        # 2. Both signals → HYBRID
        if sql_score >= 1 and rag_score >= 1 and structured_sources and doc_sources:
            return RouterDecision(
                query_type=QueryType.HYBRID,
                confidence=0.75,
                reason=f"SQL signals ({sql_score}) and RAG signals ({rag_score}) both present",
                suggested_sources=structured_sources + doc_sources,
            )

        # 3. SQL dominates
        if sql_score > rag_score and structured_sources:
            return RouterDecision(
                query_type=QueryType.NL2SQL,
                confidence=min(0.6 + sql_score * 0.1, 0.95),
                reason=f"SQL signals detected ({sql_score} matches)",
                suggested_sources=structured_sources,
            )

        # 4. RAG dominates
        if rag_score > 0 and doc_sources:
            return RouterDecision(
                query_type=QueryType.RAG,
                confidence=min(0.6 + rag_score * 0.1, 0.95),
                reason=f"Document signals detected ({rag_score} matches)",
                suggested_sources=doc_sources,
            )

        # 5. Only structured sources available → try NL2SQL
        if structured_sources:
            return RouterDecision(
                query_type=QueryType.NL2SQL,
                confidence=0.55,
                reason="Only structured sources available — defaulting to NL2SQL",
                suggested_sources=structured_sources,
            )

        # 6. Only doc sources → RAG
        if doc_sources:
            return RouterDecision(
                query_type=QueryType.RAG,
                confidence=0.55,
                reason="Only document sources available — defaulting to RAG",
                suggested_sources=doc_sources,
            )

        # 7. Nothing connected → DIRECT
        return RouterDecision(
            query_type=QueryType.DIRECT,
            confidence=0.5,
            reason="No connected sources available",
            suggested_sources=[],
        )

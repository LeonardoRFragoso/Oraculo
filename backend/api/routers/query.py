"""
Query Router — Sprint 3

POST /api/query          Universal question endpoint (NL2SQL + RAG routing)
POST /api/datasources/{id}/query   Direct NL2SQL on a specific source
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from catalog.registry import DataSourceRegistry
from catalog.schema_discovery import SchemaDiscovery
from connectors.base import DatasetInfo, ColumnInfo, ConnectorType, DataDomain
from nl2sql.engine import NL2SQLEngine
from nl2sql.validator import SQLValidator
from nl2sql.executor import SQLExecutor
from nl2sql.router import QueryRouter, QueryType
from rag.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)
router = APIRouter()

# Singletons
_registry = DataSourceRegistry()
_nl2sql = NL2SQLEngine()
_executor = SQLExecutor()
_query_router = QueryRouter()
_hybrid = HybridRetriever()


class QueryRequest(BaseModel):
    question: str
    source_ids: Optional[List[str]] = None   # None = use all connected sources
    explain: bool = True                      # include SQL explanation in response


class QueryResponse(BaseModel):
    question: str
    query_type: str
    answer: Optional[str] = None
    sql: Optional[str] = None
    sql_explanation: Optional[str] = None
    sql_confidence: float = 0.0
    sql_assumptions: List[str] = []
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    truncated: bool = False
    sources_used: List[str] = []
    warnings: List[str] = []
    error: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
async def universal_query(request: QueryRequest):
    """
    Universal question endpoint.

    Automatically routes to:
    - NL2SQL  if question is about structured data
    - RAG     if question is about documents
    - HYBRID  if both are needed

    Examples:
        "Quais clientes tiveram mais receita em 2025?"
        "Qual é a margem média por produto?"
        "O que diz a cláusula 5 do contrato?"
    """
    all_sources = _registry.list()
    connected = [s for s in all_sources if s.status == "connected"]

    if request.source_ids:
        connected = [s for s in connected if s.id in request.source_ids]

    # Route the question
    decision = _query_router.route(request.question, available_sources=connected)
    logger.info(
        f"Query routed → {decision.query_type.value} "
        f"(conf={decision.confidence:.0%}) — {request.question[:60]}"
    )

    if decision.query_type == QueryType.DIRECT:
        return QueryResponse(
            question=request.question,
            query_type=decision.query_type.value,
            answer=_direct_answer(request.question, connected),
            sources_used=[],
        )

    if decision.query_type == QueryType.NL2SQL:
        return await _handle_nl2sql(request, decision, connected)

    if decision.query_type == QueryType.HYBRID:
        return await _handle_hybrid(request, decision, connected)

    if decision.query_type == QueryType.RAG:
        return await _handle_rag(request, decision, connected)

    return QueryResponse(
        question=request.question,
        query_type="unknown",
        error="Could not determine query strategy",
    )


@router.post("/datasources/{source_id}/query", response_model=QueryResponse)
async def query_datasource(source_id: str, request: QueryRequest):
    """
    Direct NL2SQL query against a specific data source.

    The question is translated to SQL using the source's schema,
    executed, and results returned.
    """
    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    if record.status != "connected":
        raise HTTPException(
            status_code=422,
            detail=f"Source not connected. Call POST /api/datasources/{source_id}/connect first.",
        )

    # Rebuild DatasetInfo from stored catalog (no re-connect needed)
    datasets = _rebuild_dataset_infos(record.datasets)
    if not datasets:
        raise HTTPException(status_code=422, detail="No schema available. Run /connect first.")

    # Determine dialect
    dialect = _dialect_for(record.connector_type)
    allowed_tables = {ds.name for ds in datasets}

    # Generate SQL
    nl2sql_result = _nl2sql.generate(
        question=request.question,
        datasets=datasets,
        dialect=dialect,
    )
    if not nl2sql_result.success:
        return QueryResponse(
            question=request.question,
            query_type=QueryType.NL2SQL.value,
            error=nl2sql_result.error,
            sources_used=[source_id],
        )

    # Validate
    validator = SQLValidator(allowed_tables=allowed_tables)
    validation = validator.validate(nl2sql_result.sql)
    if not validation.valid:
        return QueryResponse(
            question=request.question,
            query_type=QueryType.NL2SQL.value,
            sql=nl2sql_result.sql,
            error=f"SQL validation failed: {'; '.join(validation.issues)}",
            sources_used=[source_id],
        )

    # Execute
    disc = SchemaDiscovery(registry=_registry)
    try:
        connector = disc._build_connector(record)
        connector.connect()
        # For DB connectors: use execute_query; for file: pass dataframes
        if hasattr(connector, "execute_query"):
            exec_result = _executor.execute(validation.sql, connector=connector)
        else:
            extracted = connector.extract()
            exec_result = _executor.execute(
                validation.sql, dataframes=extracted.dataframes
            )
        connector.close()
    except Exception as e:
        return QueryResponse(
            question=request.question,
            query_type=QueryType.NL2SQL.value,
            sql=validation.sql,
            error=f"Execution error: {e}",
            sources_used=[source_id],
        )

    if not exec_result.success:
        return QueryResponse(
            question=request.question,
            query_type=QueryType.NL2SQL.value,
            sql=validation.sql,
            error=exec_result.error,
            sources_used=[source_id],
        )

    # Build natural language answer summary
    answer = _build_answer(request.question, exec_result, nl2sql_result.explanation)

    return QueryResponse(
        question=request.question,
        query_type=QueryType.NL2SQL.value,
        answer=answer,
        sql=validation.sql,
        sql_explanation=nl2sql_result.explanation if request.explain else None,
        sql_confidence=nl2sql_result.confidence,
        sql_assumptions=nl2sql_result.assumptions,
        columns=exec_result.columns,
        rows=exec_result.rows,
        row_count=exec_result.row_count,
        execution_time_ms=exec_result.execution_time_ms,
        truncated=exec_result.truncated,
        sources_used=[source_id],
        warnings=validation.warnings,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _handle_hybrid(request, decision, connected) -> QueryResponse:
    """Run Hybrid RAG: NL2SQL on structured + vector search on docs → LLM synthesis."""
    structured = [s for s in connected if s.connector_type in
                  ("sqlite", "postgresql", "mysql", "csv", "excel", "parquet", "json")]
    docs = [s for s in connected if s.connector_type in ("pdf", "docx", "txt", "xml")]

    result = await _hybrid.retrieve(
        question=request.question,
        structured_sources=structured or None,
        document_sources=docs or None,
    )

    sql_r = result.sql_results or {}
    return QueryResponse(
        question=request.question,
        query_type=QueryType.HYBRID.value,
        answer=result.answer,
        sql=result.sql_query,
        sql_explanation=sql_r.get("sql_explanation"),
        sql_confidence=sql_r.get("sql_confidence", 0.0),
        columns=sql_r.get("columns", []),
        rows=sql_r.get("rows", []),
        row_count=sql_r.get("row_count", 0),
        execution_time_ms=sql_r.get("execution_time_ms", 0.0),
        sources_used=result.sources_used,
        error=result.error,
    )


async def _handle_rag(request, decision, connected) -> QueryResponse:
    """Pure RAG: vector search on document sources → LLM answer."""
    doc_sources = [s for s in connected if s.id in decision.suggested_sources]
    if not doc_sources:
        doc_sources = [s for s in connected if s.connector_type in ("pdf", "docx", "txt", "xml")]

    result = await _hybrid.retrieve(
        question=request.question,
        structured_sources=None,
        document_sources=doc_sources,
    )

    return QueryResponse(
        question=request.question,
        query_type=QueryType.RAG.value,
        answer=result.answer,
        sources_used=result.sources_used,
        error=result.error,
    )


async def _handle_nl2sql(request, decision, connected) -> QueryResponse:
    """Run NL2SQL across all suggested sources (multi-source fan-out)."""
    target_ids = decision.suggested_sources or [s.id for s in connected]
    target_sources = [s for s in connected if s.id in target_ids]

    if not target_sources:
        return QueryResponse(
            question=request.question,
            query_type=decision.query_type.value,
            error="No connected structured sources found",
        )

    # Use first available source (multi-source join is Sprint 4+)
    source = target_sources[0]
    sub_request = QueryRequest(
        question=request.question,
        source_ids=[source.id],
        explain=request.explain,
    )
    return await query_datasource(source.id, sub_request)


def _rebuild_dataset_infos(datasets_dicts: List[Dict]) -> List[DatasetInfo]:
    """Reconstruct DatasetInfo objects from stored registry dicts."""
    result = []
    for d in datasets_dicts:
        cols = [
            ColumnInfo(
                name=c["name"],
                dtype=c["dtype"],
                nullable=c.get("nullable", True),
                null_count=c.get("null_count", 0),
                unique_count=c.get("unique_count", 0),
                sample_values=c.get("sample_values", []),
            )
            for c in d.get("columns", [])
        ]
        try:
            domain = DataDomain(d.get("domain", "unknown"))
        except ValueError:
            domain = DataDomain.UNKNOWN
        try:
            ctype = ConnectorType(d.get("connector_type", "csv"))
        except ValueError:
            ctype = ConnectorType.CSV

        info = DatasetInfo(
            name=d["name"],
            connector_type=ctype,
            row_count=d.get("row_count", 0),
            column_count=d.get("column_count", 0),
            columns=cols,
            domain=domain,
            domain_confidence=d.get("domain_confidence", 0.0),
            domain_signals=d.get("domain_signals", []),
        )
        result.append(info)
    return result


def _dialect_for(connector_type: str) -> str:
    mapping = {
        "postgresql": "postgresql",
        "mysql": "mysql",
        "sqlite": "sqlite",
        "csv": "duckdb",
        "excel": "duckdb",
        "parquet": "duckdb",
        "json": "duckdb",
    }
    return mapping.get(connector_type, "sqlite")


def _direct_answer(question: str, connected) -> str:
    if not connected:
        return (
            "Nenhuma fonte de dados conectada ainda. "
            "Use POST /api/datasources para conectar uma fonte."
        )
    names = ", ".join(s.name for s in connected[:5])
    return (
        f"Tenho {len(connected)} fonte(s) conectada(s): {names}. "
        "Faça uma pergunta sobre os dados e eu a responderei!"
    )


def _build_answer(question: str, result: "ExecutionResult", explanation: str) -> str:
    if result.row_count == 0:
        return f"A consulta não retornou resultados. {explanation or ''}"
    truncation = f" (mostrando {result.row_count:,} de mais registros)" if result.truncated else ""
    return (
        f"{explanation or 'Consulta executada com sucesso.'} "
        f"Retornou {result.row_count:,} registro(s){truncation} "
        f"em {result.execution_time_ms:.0f}ms."
    )

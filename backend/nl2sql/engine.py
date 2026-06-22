"""
Sprint 3 — NL2SQL Engine

Converts a natural language question into a validated SQL query
using the data catalog as grounding context.

Flow:
    question + schema_context
         ↓
    LLM (gpt-4o-mini, cheap + fast)
         ↓
    generated SQL
         ↓
    SQLValidator (safety check)
         ↓
    validated SQL + explanation

The LLM receives:
  - Table names, column names, dtypes, sample values
  - Domain classification
  - Semantic layer hints (aliases, business terms)
  - Dialect hint (sqlite / postgresql / mysql)
"""

import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert SQL analyst. Your job is to convert a natural language question into a valid SQL query.

Rules:
1. Generate ONLY a SELECT statement — never INSERT, UPDATE, DELETE, DROP, or DDL.
2. Use only the tables and columns provided in the schema context.
3. Use proper SQL syntax for the specified dialect.
4. If the question is ambiguous, generate the most reasonable query.
5. For aggregations, always include a meaningful ORDER BY.
6. Limit results to 1000 rows unless the user asks for all.
7. Use column aliases for computed fields (e.g., SUM(revenue) AS total_revenue).
8. Respond with JSON in this exact format:
{
  "sql": "<the SQL query>",
  "explanation": "<one sentence explaining what this query does>",
  "confidence": <float 0.0-1.0>,
  "assumptions": ["<any assumption made>"]
}
"""


@dataclass
class NL2SQLResult:
    success: bool
    question: str
    sql: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.0
    assumptions: List[str] = field(default_factory=list)
    dialect: str = "sqlite"
    error: Optional[str] = None
    raw_llm_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "question": self.question,
            "sql": self.sql,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "dialect": self.dialect,
            "error": self.error,
        }


class NL2SQLEngine:
    """
    Converts natural language to SQL using LLM + schema context.

    Usage:
        engine = NL2SQLEngine()
        result = engine.generate(
            question="Quais clientes tiveram mais receita em 2025?",
            datasets=[dataset_info, ...],
            dialect="sqlite"
        )
        print(result.sql)
    """

    def __init__(self, model: Optional[str] = None):
        self._model_override = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from core.llm_client import LLMClient
            self._client = LLMClient(model_override=self._model_override)
        return self._client

    def generate(
        self,
        question: str,
        datasets: List[Any],          # List[DatasetInfo]
        dialect: str = "sqlite",
        extra_context: Optional[str] = None,
    ) -> NL2SQLResult:
        """Generate SQL from a natural language question."""
        if not datasets:
            return NL2SQLResult(
                success=False,
                question=question,
                error="No datasets available. Connect a data source first.",
            )

        schema_context = self._build_schema_context(datasets, dialect)
        user_prompt = self._build_user_prompt(question, schema_context, dialect, extra_context)

        logger.info(f"NL2SQL generating for: {question[:80]}...")

        try:
            client = self._get_client()
            resp = client.chat(
                system=_SYSTEM_PROMPT,
                user=user_prompt,
                temperature=0.1,
                max_tokens=800,
                json_mode=True,
            )
            raw = resp.content.strip()
            return self._parse_response(raw, question, dialect)

        except Exception as e:
            logger.error(f"NL2SQL generation error: {e}")
            return NL2SQLResult(
                success=False,
                question=question,
                error=str(e),
                dialect=dialect,
            )

    def _build_schema_context(self, datasets: List[Any], dialect: str) -> str:
        """Build a compact schema description for the LLM prompt."""
        lines = [f"Database dialect: {dialect}\n"]
        for ds in datasets:
            lines.append(f"TABLE: {ds.name}")
            lines.append(f"  Domain: {ds.domain.value} (confidence: {ds.domain_confidence:.0%})")
            lines.append(f"  Rows: {ds.row_count:,}")
            lines.append("  Columns:")
            for col in ds.columns[:40]:   # cap at 40 cols
                samples = ", ".join(str(v) for v in col.sample_values[:3])
                nullable = " NULLABLE" if col.nullable else ""
                lines.append(
                    f"    - {col.name} ({col.dtype}){nullable}"
                    + (f"  [e.g. {samples}]" if samples else "")
                )
            lines.append("")
        return "\n".join(lines)

    def _build_user_prompt(
        self,
        question: str,
        schema_context: str,
        dialect: str,
        extra_context: Optional[str],
    ) -> str:
        parts = [
            "=== SCHEMA ===",
            schema_context,
        ]
        if extra_context:
            parts += ["=== ADDITIONAL CONTEXT ===", extra_context]
        parts += [
            "=== QUESTION ===",
            question,
            "",
            f"Generate a {dialect.upper()} SQL query to answer this question. "
            "Return JSON with keys: sql, explanation, confidence, assumptions.",
        ]
        return "\n".join(parts)

    def _parse_response(self, raw: str, question: str, dialect: str) -> NL2SQLResult:
        import json
        try:
            data = json.loads(raw)
            sql = data.get("sql", "").strip()
            # Clean up markdown code fences if present
            sql = re.sub(r"```(?:sql)?", "", sql).strip("`").strip()

            if not sql:
                return NL2SQLResult(
                    success=False,
                    question=question,
                    error="LLM returned empty SQL",
                    raw_llm_response=raw,
                )

            return NL2SQLResult(
                success=True,
                question=question,
                sql=sql,
                explanation=data.get("explanation", ""),
                confidence=float(data.get("confidence", 0.8)),
                assumptions=data.get("assumptions", []),
                dialect=dialect,
                raw_llm_response=raw,
            )
        except Exception as e:
            logger.error(f"Failed to parse NL2SQL response: {e}\nRaw: {raw}")
            return NL2SQLResult(
                success=False,
                question=question,
                error=f"Failed to parse LLM response: {e}",
                raw_llm_response=raw,
                dialect=dialect,
            )

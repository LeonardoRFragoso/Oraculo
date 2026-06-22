"""
SQL Executor — runs a validated SQL query on the appropriate connector.

Handles:
  - SQLite, PostgreSQL, MySQL via their respective connectors
  - DataFrame-based fallback for file sources (CSV, Excel, Parquet)
    using DuckDB in-memory (no extra server needed)
  - Result serialization: DataFrame → JSON-serializable dict
  - Execution time tracking
  - Row limit enforcement
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    sql: str
    rows: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    truncated: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "sql": self.sql,
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "truncated": self.truncated,
            "error": self.error,
        }


class SQLExecutor:
    """
    Executes validated SQL queries against a data source.

    For database connectors (SQLite, PostgreSQL, MySQL):
        Uses the connector's native execute_query() method.

    For file-based sources (CSV, Excel, Parquet, JSON):
        Loads DataFrames into an in-memory DuckDB instance and
        runs SQL directly — zero server overhead.

    Usage:
        executor = SQLExecutor()
        result = executor.execute(sql, connector, dataframes)
    """

    MAX_RESULT_ROWS = 1_000

    def execute(
        self,
        sql: str,
        connector=None,
        dataframes: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> ExecutionResult:
        """
        Execute SQL and return an ExecutionResult.

        Args:
            sql: Validated SQL string.
            connector: A DataConnector instance with execute_query() (DB sources).
            dataframes: Dict of DataFrames for file-based sources.
        """
        start = time.perf_counter()

        try:
            # DB connectors: PostgreSQL, MySQL, SQLite
            if connector is not None and hasattr(connector, "execute_query"):
                df = connector.execute_query(sql)
            # File-based: use DuckDB in-memory
            elif dataframes:
                df = self._execute_on_dataframes(sql, dataframes)
            else:
                return ExecutionResult(
                    success=False,
                    sql=sql,
                    error="No connector or dataframes available for execution",
                )

            elapsed = (time.perf_counter() - start) * 1000
            return self._df_to_result(df, sql, elapsed)

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"SQL execution error: {e}\nSQL: {sql}")
            return ExecutionResult(
                success=False,
                sql=sql,
                error=str(e),
                execution_time_ms=elapsed,
            )

    def _execute_on_dataframes(
        self, sql: str, dataframes: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Execute SQL against in-memory DataFrames using DuckDB."""
        try:
            import duckdb
        except ImportError:
            raise RuntimeError(
                "duckdb not installed. Run: pip install duckdb"
            )

        con = duckdb.connect(database=":memory:")
        try:
            for name, df in dataframes.items():
                # Register DataFrame as a virtual table
                con.register(name, df)
                logger.debug(f"Registered DuckDB table: {name} ({len(df)} rows)")
            result_df = con.execute(sql).df()
            return result_df
        finally:
            con.close()

    def _df_to_result(
        self, df: pd.DataFrame, sql: str, elapsed: float
    ) -> ExecutionResult:
        truncated = len(df) > self.MAX_RESULT_ROWS
        if truncated:
            df = df.head(self.MAX_RESULT_ROWS)

        # Serialize: handle non-JSON-native types (dates, NaN, numpy scalars)
        df = df.copy()
        for col in df.columns:
            df[col] = df[col].apply(self._serialize_value)

        rows = df.to_dict(orient="records")
        return ExecutionResult(
            success=True,
            sql=sql,
            rows=rows,
            columns=list(df.columns),
            row_count=len(rows),
            execution_time_ms=elapsed,
            truncated=truncated,
        )

    @staticmethod
    def _serialize_value(val: Any) -> Any:
        import math
        import numpy as np
        if val is None:
            return None
        if isinstance(val, float) and math.isnan(val):
            return None
        if isinstance(val, (np.integer,)):
            return int(val)
        if isinstance(val, (np.floating,)):
            return float(val)
        if hasattr(val, "isoformat"):
            return val.isoformat()
        if isinstance(val, (pd.Timestamp,)):
            return val.isoformat()
        return val

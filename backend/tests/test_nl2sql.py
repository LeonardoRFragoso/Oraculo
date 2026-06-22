"""
Tests — NL2SQL: validator, executor (DuckDB), router heuristics.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

_BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(_BACKEND))


# ── SQL Validator ──────────────────────────────────────────────────────────────

class TestSQLValidator:
    @pytest.fixture(autouse=True)
    def validator(self):
        from nl2sql.validator import SQLValidator
        self.v = SQLValidator(allowed_tables={"customers", "orders", "products"})

    def test_valid_select(self):
        r = self.v.validate("SELECT id, name FROM customers")
        assert r.valid
        assert r.sql is not None

    def test_limit_auto_added(self):
        r = self.v.validate("SELECT * FROM customers")
        assert r.valid
        assert "LIMIT" in r.sql.upper()

    def test_select_star_warning(self):
        r = self.v.validate("SELECT * FROM customers LIMIT 10")
        assert r.valid
        assert any("SELECT *" in w for w in r.warnings)

    def test_drop_blocked(self):
        r = self.v.validate("DROP TABLE customers")
        assert not r.valid
        assert r.issues

    def test_insert_blocked(self):
        r = self.v.validate("INSERT INTO customers VALUES (1, 'x')")
        assert not r.valid

    def test_delete_blocked(self):
        r = self.v.validate("DELETE FROM orders WHERE id = 1")
        assert not r.valid

    def test_update_blocked(self):
        r = self.v.validate("UPDATE orders SET status='closed' WHERE id=1")
        assert not r.valid

    def test_stacked_queries_blocked(self):
        r = self.v.validate("SELECT 1; DROP TABLE customers")
        assert not r.valid

    def test_xp_cmdshell_blocked(self):
        r = self.v.validate("SELECT xp_cmdshell('ls')")
        assert not r.valid

    def test_cte_allowed(self):
        r = self.v.validate("WITH t AS (SELECT 1 AS n) SELECT n FROM t")
        assert r.valid

    def test_unknown_table_warns(self):
        r = self.v.validate("SELECT * FROM unknown_table LIMIT 10")
        assert r.valid
        assert any("unknown_table" in w for w in r.warnings)

    def test_empty_sql_rejected(self):
        r = self.v.validate("")
        assert not r.valid


# ── SQL Executor (DuckDB) ──────────────────────────────────────────────────────

class TestSQLExecutor:
    @pytest.fixture(autouse=True)
    def executor_and_data(self):
        from nl2sql.executor import SQLExecutor
        self.exec = SQLExecutor()
        self.df = pd.DataFrame({
            "customer": ["Alice", "Bob", "Alice", "Carol"],
            "product": ["A", "B", "A", "C"],
            "amount": [100.0, 250.0, 75.0, 300.0],
        })
        self.dataframes = {"sales": self.df}

    def test_basic_select(self):
        r = self.exec.execute("SELECT * FROM sales LIMIT 10", dataframes=self.dataframes)
        assert r.success
        assert r.row_count == 4
        assert "customer" in r.columns

    def test_aggregation(self):
        r = self.exec.execute(
            "SELECT customer, SUM(amount) AS total FROM sales GROUP BY customer ORDER BY total DESC LIMIT 10",
            dataframes=self.dataframes,
        )
        assert r.success
        assert r.row_count == 3  # Alice, Bob, Carol
        totals = {row["customer"]: row["total"] for row in r.rows}
        assert totals["Carol"] == 300.0
        assert totals["Alice"] == 175.0

    def test_no_connector_no_df_returns_error(self):
        from nl2sql.executor import SQLExecutor
        r = SQLExecutor().execute("SELECT 1", connector=None, dataframes=None)
        assert not r.success
        assert r.error

    def test_row_limit_enforced(self):
        from nl2sql.executor import SQLExecutor
        big_df = pd.DataFrame({"x": range(2000)})
        r = SQLExecutor().execute(
            "SELECT * FROM big LIMIT 2000", dataframes={"big": big_df}
        )
        assert r.success
        assert r.row_count <= SQLExecutor.MAX_RESULT_ROWS
        assert r.truncated

    def test_nan_serialized_as_none(self):
        import numpy as np
        df = pd.DataFrame({"val": [1.0, float("nan"), 3.0]})
        r = self.exec.execute("SELECT * FROM nan_df LIMIT 10", dataframes={"nan_df": df})
        assert r.success
        vals = [row["val"] for row in r.rows]
        assert None in vals


# ── Query Router ──────────────────────────────────────────────────────────────

class TestQueryRouter:
    @pytest.fixture(autouse=True)
    def router(self):
        from nl2sql.router import QueryRouter, QueryType
        self.router = QueryRouter()
        self.QueryType = QueryType

    def test_aggregation_routes_nl2sql(self):
        d = self.router.route("Qual é o total de vendas por cliente?", [])
        assert d.query_type == self.QueryType.NL2SQL

    def test_document_routes_rag(self):
        d = self.router.route("O que diz a cláusula 5 do contrato?", [])
        assert d.query_type == self.QueryType.RAG

    def test_direct_greeting(self):
        d = self.router.route("Olá, tudo bem?", [])
        assert d.query_type == self.QueryType.DIRECT

    def test_confidence_between_0_and_1(self):
        d = self.router.route("Quais produtos vendemos?", [])
        assert 0.0 <= d.confidence <= 1.0

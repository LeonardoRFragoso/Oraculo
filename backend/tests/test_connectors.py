"""
Tests — Connectors: CSV, Excel, JSON, Parquet (file-based).
No external DB required.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

_BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(_BACKEND))


# ── CSV Connector ──────────────────────────────────────────────────────────────

class TestCSVConnector:
    def test_connect_success(self, sample_csv):
        from connectors.files.csv_connector import CSVConnector
        c = CSVConnector(config={"path": str(sample_csv)})
        assert c.connect() is True

    def test_connect_missing_file(self, tmp_data_dir):
        from connectors.files.csv_connector import CSVConnector
        c = CSVConnector(config={"path": str(tmp_data_dir / "nonexistent.csv")})
        assert c.connect() is False

    def test_discover_returns_dataset(self, sample_csv):
        from connectors.files.csv_connector import CSVConnector
        c = CSVConnector(config={"path": str(sample_csv)})
        c.connect()
        datasets = c.discover()
        assert len(datasets) == 1
        ds = datasets[0]
        assert ds.row_count == 5
        assert ds.column_count == 5

    def test_discover_column_names(self, sample_csv):
        from connectors.files.csv_connector import CSVConnector
        c = CSVConnector(config={"path": str(sample_csv)})
        c.connect()
        datasets = c.discover()
        names = [col.name for col in datasets[0].columns]
        assert "customer" in names
        assert "amount" in names

    def test_extract_returns_dataframe(self, sample_csv):
        from connectors.files.csv_connector import CSVConnector
        c = CSVConnector(config={"path": str(sample_csv)})
        c.connect()
        result = c.extract()
        assert result.success
        assert len(result.dataframes) == 1
        df = list(result.dataframes.values())[0]
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5


# ── Excel Connector ────────────────────────────────────────────────────────────

class TestExcelConnector:
    def test_connect_success(self, sample_excel):
        from connectors.files.excel_connector import ExcelConnector
        c = ExcelConnector(config={"path": str(sample_excel)})
        assert c.connect() is True

    def test_discover_sheets(self, sample_excel):
        from connectors.files.excel_connector import ExcelConnector
        c = ExcelConnector(config={"path": str(sample_excel)})
        c.connect()
        datasets = c.discover()
        assert len(datasets) >= 1
        assert datasets[0].column_count == 4

    def test_extract_dataframe(self, sample_excel):
        from connectors.files.excel_connector import ExcelConnector
        c = ExcelConnector(config={"path": str(sample_excel)})
        c.connect()
        result = c.extract()
        assert result.success
        df = list(result.dataframes.values())[0]
        assert len(df) == 3


# ── JSON Connector ─────────────────────────────────────────────────────────────

class TestJSONConnector:
    @pytest.fixture
    def json_file(self, tmp_data_dir):
        path = tmp_data_dir / "orders.json"
        path.write_text(json.dumps([
            {"order_id": 1, "product": "A", "qty": 2},
            {"order_id": 2, "product": "B", "qty": 5},
        ]))
        return path

    def test_connect_success(self, json_file):
        from connectors.files.json_connector import JSONConnector
        c = JSONConnector(config={"path": str(json_file)})
        assert c.connect() is True

    def test_discover(self, json_file):
        from connectors.files.json_connector import JSONConnector
        c = JSONConnector(config={"path": str(json_file)})
        c.connect()
        datasets = c.discover()
        assert len(datasets) >= 1

    def test_extract(self, json_file):
        from connectors.files.json_connector import JSONConnector
        c = JSONConnector(config={"path": str(json_file)})
        c.connect()
        result = c.extract()
        assert result.success


# ── Semantic Engine ────────────────────────────────────────────────────────────

class TestSemanticEngine:
    @pytest.fixture(autouse=True)
    def engine(self):
        from catalog.semantic_engine import SemanticEngine
        self.engine = SemanticEngine(llm_fallback=False)

    def _make_dataset(self, name, columns):
        from connectors.base import DatasetInfo, ColumnInfo, ConnectorType
        cols = [ColumnInfo(name=c, dtype="str") for c in columns]
        return DatasetInfo(name=name, connector_type=ConnectorType.CSV, columns=cols)

    def test_financial_classification(self):
        ds = self._make_dataset("ledger", ["invoice_id", "amount", "revenue", "payment_date"])
        result = self.engine.classify(ds)
        assert result.domain.value in ("financial", "ecommerce", "crm")

    def test_hr_classification(self):
        ds = self._make_dataset("employees", ["employee_id", "salary", "department", "hire_date"])
        result = self.engine.classify(ds)
        assert result.domain.value == "hr"

    def test_logistics_classification(self):
        ds = self._make_dataset("shipments", ["shipment_id", "carrier", "delivery_date", "warehouse"])
        result = self.engine.classify(ds)
        assert result.domain.value == "logistics"

    def test_confidence_in_range(self):
        ds = self._make_dataset("misc", ["col_a", "col_b"])
        result = self.engine.classify(ds)
        assert 0.0 <= result.confidence <= 1.0

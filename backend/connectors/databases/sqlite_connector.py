import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base import (
    ColumnInfo, ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)


class SQLiteConnector(DataConnector):
    """
    Connector for SQLite databases.

    config keys:
        path (str): path to .db / .sqlite file
        max_rows (int): row limit per table extract (default 100_000)
    """

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.SQLITE

    def connect(self) -> bool:
        path = Path(self.config["path"])
        if not path.exists():
            logger.error(f"SQLite database not found: {path}")
            return False
        try:
            conn = sqlite3.connect(str(path))
            conn.execute("SELECT 1")
            conn.close()
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"SQLite connect error: {e}")
            return False

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.config["path"]))

    def discover(self) -> List[DatasetInfo]:
        datasets = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                try:
                    df_sample = pd.read_sql(f"SELECT * FROM [{table}] LIMIT 200", conn)
                    row_count = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
                    datasets.append(DatasetInfo(
                        name=table,
                        connector_type=self.connector_type,
                        row_count=row_count,
                        column_count=len(df_sample.columns),
                        columns=self._infer_column_info(df_sample),
                        source_path=self.config["path"],
                        extra={"database": Path(self.config["path"]).stem},
                    ))
                except Exception as e:
                    logger.warning(f"Could not introspect table {table}: {e}")
            conn.close()
        except Exception as e:
            logger.error(f"SQLite discover error: {e}")
        return datasets

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        max_rows = self.config.get("max_rows", 100_000)
        try:
            conn = self._get_connection()
            datasets = self.discover()
            tables_to_extract = [dataset_name] if dataset_name else [d.name for d in datasets]
            dataframes: Dict[str, pd.DataFrame] = {}

            for table in tables_to_extract:
                try:
                    df = pd.read_sql(f"SELECT * FROM [{table}] LIMIT {max_rows}", conn)
                    dataframes[table] = df
                except Exception as e:
                    logger.warning(f"Could not extract table {table}: {e}")

            conn.close()
            filtered = [d for d in datasets if not dataset_name or d.name == dataset_name]
            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=filtered,
                dataframes=dataframes,
                metadata={"tables": list(dataframes.keys())},
            )
        except Exception as e:
            logger.error(f"SQLite extract error: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute arbitrary SQL and return a DataFrame. Used by NL2SQL engine."""
        conn = self._get_connection()
        try:
            df = pd.read_sql(sql, conn)
            return df
        finally:
            conn.close()

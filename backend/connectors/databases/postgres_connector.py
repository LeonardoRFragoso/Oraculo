import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base import (
    ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)


class PostgreSQLConnector(DataConnector):
    """
    Connector for PostgreSQL databases.

    config keys:
        host (str): default 'localhost'
        port (int): default 5432
        database (str): required
        user (str): required
        password (str): required
        schema (str): default 'public'
        max_rows (int): row limit per table (default 100_000)
        ssl (bool): use SSL (default False)
    """

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.POSTGRESQL

    def _get_engine(self):
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise RuntimeError("sqlalchemy not installed. Run: pip install sqlalchemy psycopg2-binary")

        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        db = self.config["database"]
        user = self.config["user"]
        password = self.config["password"]
        ssl = "?sslmode=require" if self.config.get("ssl") else ""
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}{ssl}"
        return create_engine(url)

    def connect(self) -> bool:
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            self._connected = True
            logger.info(f"PostgreSQL connected: {self.config.get('host')}:{self.config.get('port', 5432)}/{self.config['database']}")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connect error: {e}")
            return False

    def discover(self) -> List[DatasetInfo]:
        schema = self.config.get("schema", "public")
        datasets = []
        try:
            engine = self._get_engine()
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names(schema=schema)
            views = inspector.get_view_names(schema=schema)

            for table in tables + views:
                try:
                    df_sample = pd.read_sql(
                        f'SELECT * FROM "{schema}"."{table}" LIMIT 200',
                        engine
                    )
                    row_count_df = pd.read_sql(
                        f'SELECT COUNT(*) as cnt FROM "{schema}"."{table}"',
                        engine
                    )
                    row_count = int(row_count_df["cnt"].iloc[0])

                    datasets.append(DatasetInfo(
                        name=table,
                        connector_type=self.connector_type,
                        row_count=row_count,
                        column_count=len(df_sample.columns),
                        columns=self._infer_column_info(df_sample),
                        source_path=f"{self.config.get('host')}/{self.config['database']}/{schema}/{table}",
                        extra={"schema": schema, "database": self.config["database"]},
                    ))
                except Exception as e:
                    logger.warning(f"Could not introspect {table}: {e}")
        except Exception as e:
            logger.error(f"PostgreSQL discover error: {e}")
        return datasets

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        schema = self.config.get("schema", "public")
        max_rows = self.config.get("max_rows", 100_000)
        try:
            engine = self._get_engine()
            datasets = self.discover()
            tables_to_extract = [dataset_name] if dataset_name else [d.name for d in datasets]
            dataframes: Dict[str, pd.DataFrame] = {}

            for table in tables_to_extract:
                try:
                    df = pd.read_sql(
                        f'SELECT * FROM "{schema}"."{table}" LIMIT {max_rows}',
                        engine
                    )
                    dataframes[table] = df
                except Exception as e:
                    logger.warning(f"Could not extract {table}: {e}")

            filtered = [d for d in datasets if not dataset_name or d.name == dataset_name]
            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=filtered,
                dataframes=dataframes,
                metadata={"tables": list(dataframes.keys()), "schema": schema},
            )
        except Exception as e:
            logger.error(f"PostgreSQL extract error: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute arbitrary SQL. Used by NL2SQL engine."""
        engine = self._get_engine()
        return pd.read_sql(sql, engine)

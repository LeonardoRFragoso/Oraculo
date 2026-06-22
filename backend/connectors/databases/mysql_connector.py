import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base import (
    ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)


class MySQLConnector(DataConnector):
    """
    Connector for MySQL / MariaDB databases.

    config keys:
        host (str): default 'localhost'
        port (int): default 3306
        database (str): required
        user (str): required
        password (str): required
        max_rows (int): row limit per table (default 100_000)
    """

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.MYSQL

    def _get_engine(self):
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise RuntimeError("sqlalchemy not installed. Run: pip install sqlalchemy pymysql")

        host = self.config.get("host", "localhost")
        port = self.config.get("port", 3306)
        db = self.config["database"]
        user = self.config["user"]
        password = self.config["password"]
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
        return create_engine(url)

    def connect(self) -> bool:
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            self._connected = True
            logger.info(f"MySQL connected: {self.config.get('host')}/{self.config['database']}")
            return True
        except Exception as e:
            logger.error(f"MySQL connect error: {e}")
            return False

    def discover(self) -> List[DatasetInfo]:
        db = self.config["database"]
        datasets = []
        try:
            engine = self._get_engine()
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names(schema=db)
            views = inspector.get_view_names(schema=db)

            for table in tables + views:
                try:
                    df_sample = pd.read_sql(
                        f"SELECT * FROM `{table}` LIMIT 200",
                        engine
                    )
                    row_count_df = pd.read_sql(
                        f"SELECT COUNT(*) as cnt FROM `{table}`",
                        engine
                    )
                    row_count = int(row_count_df["cnt"].iloc[0])

                    datasets.append(DatasetInfo(
                        name=table,
                        connector_type=self.connector_type,
                        row_count=row_count,
                        column_count=len(df_sample.columns),
                        columns=self._infer_column_info(df_sample),
                        source_path=f"{self.config.get('host')}/{db}/{table}",
                        extra={"database": db},
                    ))
                except Exception as e:
                    logger.warning(f"Could not introspect {table}: {e}")
        except Exception as e:
            logger.error(f"MySQL discover error: {e}")
        return datasets

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        db = self.config["database"]
        max_rows = self.config.get("max_rows", 100_000)
        try:
            engine = self._get_engine()
            datasets = self.discover()
            tables_to_extract = [dataset_name] if dataset_name else [d.name for d in datasets]
            dataframes: Dict[str, pd.DataFrame] = {}

            for table in tables_to_extract:
                try:
                    df = pd.read_sql(f"SELECT * FROM `{table}` LIMIT {max_rows}", engine)
                    dataframes[table] = df
                except Exception as e:
                    logger.warning(f"Could not extract {table}: {e}")

            filtered = [d for d in datasets if not dataset_name or d.name == dataset_name]
            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=filtered,
                dataframes=dataframes,
                metadata={"tables": list(dataframes.keys()), "database": db},
            )
        except Exception as e:
            logger.error(f"MySQL extract error: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute arbitrary SQL. Used by NL2SQL engine."""
        engine = self._get_engine()
        return pd.read_sql(sql, engine)

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base import (
    ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)


class ParquetConnector(DataConnector):
    """
    Connector for Apache Parquet files.

    config keys:
        path (str): file path
        columns (list[str]|None): column subset for projection pushdown
        max_rows (int): optional row limit
    """

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.PARQUET

    def connect(self) -> bool:
        path = Path(self.config["path"])
        if not path.exists():
            logger.error(f"Parquet file not found: {path}")
            return False
        try:
            import pyarrow.parquet as pq  # noqa: F401
        except ImportError:
            logger.error("pyarrow not installed. Run: pip install pyarrow")
            return False
        self._connected = True
        return True

    def discover(self) -> List[DatasetInfo]:
        path = Path(self.config["path"])
        try:
            import pyarrow.parquet as pq
            pf = pq.ParquetFile(path)
            schema = pf.schema_arrow
            meta = pf.metadata
            df_sample = pf.read_row_group(0).to_pandas().head(200)
            columns = self._infer_column_info(df_sample)
            return [DatasetInfo(
                name=path.stem,
                connector_type=self.connector_type,
                row_count=meta.num_rows,
                column_count=meta.num_columns,
                columns=columns,
                size_bytes=path.stat().st_size,
                source_path=str(path),
                extra={"num_row_groups": meta.num_row_groups},
            )]
        except Exception as e:
            logger.error(f"Parquet discover error: {e}")
            return []

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        path = Path(self.config["path"])
        cols = self.config.get("columns")
        max_rows = self.config.get("max_rows")
        try:
            df = pd.read_parquet(path, columns=cols, engine="pyarrow")
            if max_rows:
                df = df.head(max_rows)
            datasets = self.discover()
            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=datasets,
                dataframes={path.stem: df},
                metadata={"rows": len(df), "cols": len(df.columns)},
            )
        except Exception as e:
            logger.error(f"Parquet extract error: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

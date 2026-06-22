import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base import (
    ColumnInfo, ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)


class CSVConnector(DataConnector):
    """
    Connector for CSV / TSV files.

    config keys:
        path (str): absolute or relative file path
        encoding (str): default 'utf-8'
        separator (str): default ','
        max_rows (int): optional row limit for extract
    """

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.CSV

    def connect(self) -> bool:
        path = Path(self.config["path"])
        if not path.exists():
            logger.error(f"CSV file not found: {path}")
            return False
        self._connected = True
        return True

    def discover(self) -> List[DatasetInfo]:
        path = Path(self.config["path"])
        sep = self.config.get("separator", ",")
        encoding = self.config.get("encoding", "utf-8")

        try:
            df = pd.read_csv(path, sep=sep, encoding=encoding, nrows=200)
            full_df = pd.read_csv(path, sep=sep, encoding=encoding, usecols=[0])
            row_count = len(full_df)

            info = DatasetInfo(
                name=path.stem,
                connector_type=self.connector_type,
                row_count=row_count,
                column_count=len(df.columns),
                columns=self._infer_column_info(df),
                size_bytes=path.stat().st_size,
                source_path=str(path),
            )
            return [info]
        except Exception as e:
            logger.error(f"CSV discover error: {e}")
            return []

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        path = Path(self.config["path"])
        sep = self.config.get("separator", ",")
        encoding = self.config.get("encoding", "utf-8")
        max_rows = self.config.get("max_rows")

        try:
            df = pd.read_csv(path, sep=sep, encoding=encoding, nrows=max_rows)
            datasets = self.discover()

            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=datasets,
                dataframes={path.stem: df},
                metadata={"rows": len(df), "cols": len(df.columns)},
            )
        except UnicodeDecodeError:
            df = pd.read_csv(path, sep=sep, encoding="latin-1", nrows=max_rows)
            datasets = self.discover()
            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=datasets,
                dataframes={path.stem: df},
                metadata={"rows": len(df), "cols": len(df.columns), "encoding": "latin-1"},
            )
        except Exception as e:
            logger.error(f"CSV extract error: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

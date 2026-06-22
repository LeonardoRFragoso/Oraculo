import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base import (
    ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)


class JSONConnector(DataConnector):
    """
    Connector for JSON files.

    Handles:
        - Array of objects  → DataFrame
        - Nested objects    → flattened DataFrame (pd.json_normalize)
        - Arbitrary JSON    → raw_text for RAG
    """

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.JSON

    def connect(self) -> bool:
        path = Path(self.config["path"])
        if not path.exists():
            logger.error(f"JSON file not found: {path}")
            return False
        self._connected = True
        return True

    def _load_json(self, path: Path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _to_dataframe(self, data: Any) -> Optional[pd.DataFrame]:
        try:
            if isinstance(data, list):
                return pd.json_normalize(data)
            elif isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list) and val:
                        return pd.json_normalize(val)
                return pd.json_normalize([data])
        except Exception as e:
            logger.warning(f"Could not convert JSON to DataFrame: {e}")
        return None

    def discover(self) -> List[DatasetInfo]:
        path = Path(self.config["path"])
        try:
            data = self._load_json(path)
            df = self._to_dataframe(data)
            if df is not None:
                return [DatasetInfo(
                    name=path.stem,
                    connector_type=self.connector_type,
                    row_count=len(df),
                    column_count=len(df.columns),
                    columns=self._infer_column_info(df.head(200)),
                    size_bytes=path.stat().st_size,
                    source_path=str(path),
                )]
            return [DatasetInfo(
                name=path.stem,
                connector_type=self.connector_type,
                row_count=0,
                column_count=0,
                size_bytes=path.stat().st_size,
                source_path=str(path),
                extra={"note": "non-tabular JSON"},
            )]
        except Exception as e:
            logger.error(f"JSON discover error: {e}")
            return []

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        path = Path(self.config["path"])
        try:
            data = self._load_json(path)
            df = self._to_dataframe(data)
            raw_text = json.dumps(data, ensure_ascii=False, indent=2) if df is None else None
            datasets = self.discover()
            dataframes = {path.stem: df} if df is not None else {}
            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=datasets,
                dataframes=dataframes,
                raw_text=raw_text,
                metadata={"rows": len(df) if df is not None else 0},
            )
        except Exception as e:
            logger.error(f"JSON extract error: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

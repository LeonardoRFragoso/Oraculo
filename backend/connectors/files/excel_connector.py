import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..base import (
    ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)


class ExcelConnector(DataConnector):
    """
    Connector for XLSX / XLS files.

    config keys:
        path (str): file path
        sheet_name (str|None): specific sheet; None = all sheets
        max_rows (int): optional row limit per sheet
    """

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.EXCEL

    def connect(self) -> bool:
        path = Path(self.config["path"])
        if not path.exists():
            logger.error(f"Excel file not found: {path}")
            return False
        self._connected = True
        return True

    def discover(self) -> List[DatasetInfo]:
        path = Path(self.config["path"])
        try:
            xf = pd.ExcelFile(path)
            datasets = []
            for sheet in xf.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet, nrows=200)
                full_df = pd.read_excel(path, sheet_name=sheet, usecols=[0])
                datasets.append(DatasetInfo(
                    name=sheet,
                    connector_type=self.connector_type,
                    row_count=len(full_df),
                    column_count=len(df.columns),
                    columns=self._infer_column_info(df),
                    size_bytes=path.stat().st_size,
                    source_path=str(path),
                    extra={"file": path.name, "sheet": sheet},
                ))
            return datasets
        except Exception as e:
            logger.error(f"Excel discover error: {e}")
            return []

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        path = Path(self.config["path"])
        max_rows = self.config.get("max_rows")
        sheet_filter = dataset_name or self.config.get("sheet_name")

        try:
            xf = pd.ExcelFile(path)
            sheets = [sheet_filter] if sheet_filter and sheet_filter in xf.sheet_names else xf.sheet_names
            dataframes: Dict[str, pd.DataFrame] = {}
            for sheet in sheets:
                dataframes[sheet] = pd.read_excel(path, sheet_name=sheet, nrows=max_rows)

            datasets = [d for d in self.discover() if not sheet_filter or d.name == sheet_filter]
            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=datasets,
                dataframes=dataframes,
                metadata={"sheets": list(dataframes.keys())},
            )
        except Exception as e:
            logger.error(f"Excel extract error: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

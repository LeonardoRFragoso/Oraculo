"""
Base interface for all Oráculo data connectors.

Every connector must implement: connect(), discover(), extract().
The Semantic Engine runs on top of the discovery output.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import pandas as pd


class ConnectorType(str, Enum):
    # File-based
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PARQUET = "parquet"
    XML = "xml"
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    # Databases
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    SQLSERVER = "sqlserver"
    # Cloud
    GOOGLE_DRIVE = "google_drive"
    S3 = "s3"
    ONEDRIVE = "onedrive"
    # APIs
    REST = "rest"
    GRAPHQL = "graphql"


class DataDomain(str, Enum):
    """Business domain classification for the Semantic Engine."""
    FINANCIAL = "financial"
    HR = "hr"
    CRM = "crm"
    LOGISTICS = "logistics"
    ERP = "erp"
    ECOMMERCE = "ecommerce"
    MARKETING = "marketing"
    SUPPORT = "support"
    LEGAL = "legal"
    OPERATIONS = "operations"
    UNKNOWN = "unknown"


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    nullable: bool = True
    sample_values: List[Any] = field(default_factory=list)
    null_count: int = 0
    unique_count: int = 0
    description: Optional[str] = None


@dataclass
class DatasetInfo:
    """Schema and metadata discovered for a single table/sheet/file."""
    name: str
    connector_type: ConnectorType
    row_count: int
    column_count: int
    columns: List[ColumnInfo] = field(default_factory=list)
    domain: DataDomain = DataDomain.UNKNOWN
    domain_confidence: float = 0.0
    domain_signals: List[str] = field(default_factory=list)
    size_bytes: int = 0
    source_path: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "connector_type": self.connector_type.value,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [
                {
                    "name": c.name,
                    "dtype": c.dtype,
                    "nullable": c.nullable,
                    "null_count": c.null_count,
                    "unique_count": c.unique_count,
                    "sample_values": c.sample_values[:5],
                    "description": c.description,
                }
                for c in self.columns
            ],
            "domain": self.domain.value,
            "domain_confidence": self.domain_confidence,
            "domain_signals": self.domain_signals,
            "size_bytes": self.size_bytes,
            "source_path": self.source_path,
            "extra": self.extra,
        }


@dataclass
class ConnectorResult:
    """Unified output from any connector's extract() call."""
    success: bool
    connector_type: ConnectorType
    datasets: List[DatasetInfo] = field(default_factory=list)
    dataframes: Dict[str, pd.DataFrame] = field(default_factory=dict)
    raw_text: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def primary_dataset(self) -> Optional[DatasetInfo]:
        return self.datasets[0] if self.datasets else None

    @property
    def primary_dataframe(self) -> Optional[pd.DataFrame]:
        if self.dataframes:
            return next(iter(self.dataframes.values()))
        return None


class DataConnector(ABC):
    """
    Abstract base for all Oráculo connectors.

    Lifecycle:
        connector = MyConnector(config)
        connector.connect()        # Establish connection / validate file
        info = connector.discover() # Inspect schema without loading all data
        result = connector.extract() # Load data into DataFrames + text
        connector.close()
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connected = False

    @property
    @abstractmethod
    def connector_type(self) -> ConnectorType:
        ...

    @abstractmethod
    def connect(self) -> bool:
        """Validate credentials / file access. Returns True if successful."""
        ...

    @abstractmethod
    def discover(self) -> List[DatasetInfo]:
        """
        Return schema info without loading full data.
        Should be fast — used by the Semantic Engine and Catalog.
        """
        ...

    @abstractmethod
    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        """
        Load data into ConnectorResult.
        dataset_name: optional filter (e.g. specific table or sheet).
        """
        ...

    def close(self) -> None:
        """Release any held resources (connections, file handles)."""
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    @staticmethod
    def _infer_column_info(df: pd.DataFrame) -> List[ColumnInfo]:
        """Helper: build ColumnInfo list from a DataFrame."""
        columns = []
        for col in df.columns:
            series = df[col]
            sample = series.dropna().head(5).tolist()
            columns.append(ColumnInfo(
                name=str(col),
                dtype=str(series.dtype),
                nullable=bool(series.isnull().any()),
                null_count=int(series.isnull().sum()),
                unique_count=int(series.nunique()),
                sample_values=sample,
            ))
        return columns

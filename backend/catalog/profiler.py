"""
Sprint 2 — Data Profiler

Generates deep statistics for every column in a dataset:
  - Numeric:   min, max, mean, median, std, percentiles, histogram, outliers
  - Categorical: value_counts, top_values, cardinality ratio
  - Datetime:  min_date, max_date, range_days
  - Text:      avg_len, max_len, empty ratio

Also detects:
  - Null patterns
  - Duplicate rows
  - Potential PII columns (email, CPF, phone, etc.)
  - Suspicious / anomalous values
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PII signal patterns
# ---------------------------------------------------------------------------
_PII_PATTERNS = {
    "email": re.compile(r"^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z]{2,}$", re.IGNORECASE),
    "cpf": re.compile(r"^\d{3}[.\-]?\d{3}[.\-]?\d{3}[-]?\d{2}$"),
    "cnpj": re.compile(r"^\d{2}[.\-]?\d{3}[.\-]?\d{3}[/]?\d{4}[-]?\d{2}$"),
    "phone": re.compile(r"^[\+\(]?\d[\d\s\(\)\-]{7,14}\d$"),
    "credit_card": re.compile(r"^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$"),
}

_PII_COLUMN_NAMES = {
    "email", "e-mail", "mail", "cpf", "cnpj", "rg", "phone", "telefone",
    "celular", "mobile", "credit_card", "cartao", "cartão", "password",
    "senha", "secret", "token", "ssn", "passport",
}


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    col_type: str                          # numeric | categorical | datetime | text | boolean
    total_count: int
    null_count: int
    null_pct: float
    unique_count: int
    unique_pct: float
    is_constant: bool = False
    is_id_like: bool = False               # high cardinality, likely an ID
    is_pii: bool = False
    pii_type: Optional[str] = None

    # Numeric
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    p25: Optional[float] = None
    p75: Optional[float] = None
    outlier_count: int = 0
    outlier_pct: float = 0.0

    # Categorical / text
    top_values: List[Dict[str, Any]] = field(default_factory=list)   # [{value, count, pct}]
    avg_length: Optional[float] = None
    max_length: Optional[int] = None

    # Datetime
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    date_range_days: Optional[int] = None

    # Histogram bins for numeric columns (list of {bin_start, bin_end, count})
    histogram: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetProfile:
    dataset_name: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    duplicate_row_pct: float
    null_total: int
    null_pct_overall: float
    memory_usage_mb: float
    columns: List[ColumnProfile] = field(default_factory=list)
    profiled_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["columns"] = [c.to_dict() for c in self.columns]
        return d


class DataProfiler:
    """
    Profiles a pandas DataFrame and returns a DatasetProfile.

    Usage:
        profiler = DataProfiler()
        profile = profiler.profile(df, dataset_name="sales_2025")
    """

    def __init__(self, histogram_bins: int = 10, top_n: int = 10):
        self.histogram_bins = histogram_bins
        self.top_n = top_n

    def profile(self, df: pd.DataFrame, dataset_name: str = "dataset") -> DatasetProfile:
        """Run full profiling on a DataFrame."""
        logger.info(f"Profiling '{dataset_name}' — {len(df):,} rows × {len(df.columns)} cols")

        dup_count = int(df.duplicated().sum())
        null_total = int(df.isnull().sum().sum())
        total_cells = len(df) * len(df.columns)
        mem_mb = df.memory_usage(deep=True).sum() / 1_048_576

        col_profiles = []
        warnings = []

        for col in df.columns:
            series = df[col]
            try:
                cp = self._profile_column(series)
                col_profiles.append(cp)
                # Collect dataset-level warnings
                if cp.null_pct > 0.5:
                    warnings.append(f"Column '{col}' has {cp.null_pct:.0%} nulls")
                if cp.is_constant:
                    warnings.append(f"Column '{col}' is constant (zero variance)")
                if cp.is_pii:
                    warnings.append(f"Column '{col}' may contain {cp.pii_type} (PII)")
                if cp.outlier_pct > 0.05:
                    warnings.append(f"Column '{col}' has {cp.outlier_pct:.1%} outliers")
            except Exception as e:
                logger.warning(f"Could not profile column '{col}': {e}")

        if dup_count > 0:
            dup_pct = dup_count / len(df)
            if dup_pct > 0.01:
                warnings.append(f"{dup_count:,} duplicate rows ({dup_pct:.1%}) detected")

        return DatasetProfile(
            dataset_name=dataset_name,
            row_count=len(df),
            column_count=len(df.columns),
            duplicate_row_count=dup_count,
            duplicate_row_pct=round(dup_count / max(len(df), 1), 4),
            null_total=null_total,
            null_pct_overall=round(null_total / max(total_cells, 1), 4),
            memory_usage_mb=round(mem_mb, 3),
            columns=col_profiles,
            warnings=warnings,
        )

    def _profile_column(self, series: pd.Series) -> ColumnProfile:
        name = str(series.name)
        total = len(series)
        null_count = int(series.isnull().sum())
        null_pct = round(null_count / max(total, 1), 4)
        non_null = series.dropna()
        unique_count = int(series.nunique())
        unique_pct = round(unique_count / max(total, 1), 4)
        is_constant = unique_count <= 1
        is_id_like = unique_pct > 0.95 and unique_count > 10

        col_type, dtype_str = self._infer_type(series)
        pii_type = self._detect_pii(series, name)

        cp = ColumnProfile(
            name=name,
            dtype=dtype_str,
            col_type=col_type,
            total_count=total,
            null_count=null_count,
            null_pct=null_pct,
            unique_count=unique_count,
            unique_pct=unique_pct,
            is_constant=is_constant,
            is_id_like=is_id_like,
            is_pii=pii_type is not None,
            pii_type=pii_type,
        )

        if col_type == "numeric":
            self._fill_numeric(cp, non_null)
        elif col_type == "datetime":
            self._fill_datetime(cp, non_null)
        else:
            self._fill_categorical(cp, non_null, col_type)

        return cp

    def _infer_type(self, series: pd.Series):
        dtype = series.dtype
        dtype_str = str(dtype)

        if pd.api.types.is_bool_dtype(dtype):
            return "boolean", dtype_str
        if pd.api.types.is_numeric_dtype(dtype):
            return "numeric", dtype_str
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "datetime", dtype_str

        # Try to parse as datetime
        if series.dtype == object:
            sample = series.dropna().head(20)
            try:
                pd.to_datetime(sample, infer_datetime_format=True)
                return "datetime", "datetime_str"
            except Exception:
                pass

        # Text vs categorical: if avg length > 50, treat as text
        if series.dtype == object:
            avg_len = series.dropna().astype(str).str.len().mean()
            if avg_len and avg_len > 50:
                return "text", dtype_str

        return "categorical", dtype_str

    def _fill_numeric(self, cp: ColumnProfile, series: pd.Series):
        if len(series) == 0:
            return
        arr = pd.to_numeric(series, errors="coerce").dropna()
        if len(arr) == 0:
            return

        q1, q3 = arr.quantile(0.25), arr.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = arr[(arr < lower) | (arr > upper)]

        cp.min_val = round(float(arr.min()), 6)
        cp.max_val = round(float(arr.max()), 6)
        cp.mean = round(float(arr.mean()), 6)
        cp.median = round(float(arr.median()), 6)
        cp.std = round(float(arr.std()), 6)
        cp.p25 = round(float(q1), 6)
        cp.p75 = round(float(q3), 6)
        cp.outlier_count = len(outliers)
        cp.outlier_pct = round(len(outliers) / max(len(arr), 1), 4)

        # Histogram
        try:
            counts, edges = np.histogram(arr, bins=self.histogram_bins)
            cp.histogram = [
                {"bin_start": round(float(edges[i]), 4),
                 "bin_end": round(float(edges[i + 1]), 4),
                 "count": int(counts[i])}
                for i in range(len(counts))
            ]
        except Exception:
            pass

    def _fill_datetime(self, cp: ColumnProfile, series: pd.Series):
        try:
            dt = pd.to_datetime(series, errors="coerce").dropna()
            if len(dt) == 0:
                return
            cp.min_date = str(dt.min().date())
            cp.max_date = str(dt.max().date())
            cp.date_range_days = (dt.max() - dt.min()).days
        except Exception:
            pass

    def _fill_categorical(self, cp: ColumnProfile, series: pd.Series, col_type: str):
        if len(series) == 0:
            return
        str_series = series.astype(str)

        # Top values
        vc = str_series.value_counts().head(self.top_n)
        total = len(str_series)
        cp.top_values = [
            {"value": str(val), "count": int(cnt), "pct": round(cnt / total, 4)}
            for val, cnt in vc.items()
        ]

        # Text length stats
        lengths = str_series.str.len()
        cp.avg_length = round(float(lengths.mean()), 2)
        cp.max_length = int(lengths.max())

    def _detect_pii(self, series: pd.Series, col_name: str) -> Optional[str]:
        # Check column name first (fast)
        col_lower = col_name.lower().replace("-", "_").replace(" ", "_")
        for pii_type in _PII_COLUMN_NAMES:
            if pii_type in col_lower:
                return pii_type

        # Sample-based pattern matching for object columns
        if series.dtype != object:
            return None
        sample = series.dropna().head(10).astype(str)
        for pii_type, pattern in _PII_PATTERNS.items():
            matches = sample.apply(lambda v: bool(pattern.match(v))).sum()
            if matches >= min(3, len(sample)):
                return pii_type
        return None

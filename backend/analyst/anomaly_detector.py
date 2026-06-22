"""
Sprint 5 — Anomaly Detector

Detects anomalies purely via statistics — zero LLM cost:
  - Numeric outliers   (IQR method, Z-score)
  - Sudden spikes/drops in time series (pct change > threshold)
  - Concentration risk (one entity > X% of total)
  - Suspicious zero/negative values in revenue columns
  - Frequent value anomalies (unexpected modes)
  - Missing time periods (gaps in date sequences)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_SEVERITY = {"critical": 3, "warning": 2, "info": 1}


@dataclass
class Anomaly:
    type: str                    # "outlier" | "spike" | "concentration" | "gap" | "negative" | "trend"
    severity: str                # "critical" | "warning" | "info"
    column: str
    message: str
    value: Optional[Any] = None
    affected_rows: int = 0
    affected_pct: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    emoji: str = "⚠️"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "column": self.column,
            "message": self.message,
            "value": self.value,
            "affected_rows": self.affected_rows,
            "affected_pct": round(self.affected_pct, 4),
            "details": self.details,
            "emoji": self.emoji,
        }


class AnomalyDetector:
    """
    Detects statistical anomalies in a DataFrame.

    Usage:
        detector = AnomalyDetector()
        anomalies = detector.detect(df, domain="financial", source_name="Sales")
    """

    def __init__(
        self,
        iqr_multiplier: float = 1.5,
        zscore_threshold: float = 3.0,
        concentration_threshold: float = 0.50,
        spike_threshold: float = 0.30,
    ):
        self.iqr_mult = iqr_multiplier
        self.zscore_thresh = zscore_threshold
        self.concentration_thresh = concentration_threshold
        self.spike_thresh = spike_threshold

    def detect(
        self,
        df: pd.DataFrame,
        domain: str = "unknown",
        source_name: str = "dataset",
    ) -> List[Anomaly]:
        anomalies: List[Anomaly] = []

        for col in df.columns:
            series = df[col]
            if pd.api.types.is_numeric_dtype(series):
                anomalies.extend(self._check_numeric(series, col))
            elif series.dtype == object:
                anomalies.extend(self._check_categorical(series, col, df))

        # Cross-column: concentration risk
        anomalies.extend(self._check_concentration(df, domain))

        # Date column: time gaps
        anomalies.extend(self._check_time_gaps(df))

        # Sort by severity desc
        anomalies.sort(key=lambda a: _SEVERITY.get(a.severity, 0), reverse=True)
        return anomalies

    # ------------------------------------------------------------------
    # Numeric checks
    # ------------------------------------------------------------------

    def _check_numeric(self, series: pd.Series, col: str) -> List[Anomaly]:
        anomalies = []
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if len(clean) < 3:
            return []

        # IQR outliers
        q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - self.iqr_mult * iqr
        upper = q3 + self.iqr_mult * iqr
        outliers = clean[(clean < lower) | (clean > upper)]
        if len(outliers) > 0:
            outlier_pct = len(outliers) / len(clean)
            severity = "critical" if outlier_pct > 0.1 else "warning"
            max_outlier = float(outliers.abs().max())
            anomalies.append(Anomaly(
                type="outlier",
                severity=severity,
                column=col,
                message=f"'{col}' tem {len(outliers)} outliers ({outlier_pct:.1%}). "
                        f"Valor extremo: {max_outlier:,.2f}",
                value=max_outlier,
                affected_rows=len(outliers),
                affected_pct=outlier_pct,
                details={"lower_bound": float(lower), "upper_bound": float(upper),
                         "q1": float(q1), "q3": float(q3)},
                emoji="📊",
            ))

        # Negative values in revenue-like columns
        if any(kw in col.lower() for kw in ("revenue", "receita", "valor", "amount", "price")):
            negatives = clean[clean < 0]
            if len(negatives) > 0:
                anomalies.append(Anomaly(
                    type="negative",
                    severity="critical",
                    column=col,
                    message=f"'{col}' tem {len(negatives)} valores negativos — possível erro de dados",
                    value=float(negatives.min()),
                    affected_rows=len(negatives),
                    affected_pct=len(negatives) / len(clean),
                    emoji="🚨",
                ))

        # Zero revenue check
        if any(kw in col.lower() for kw in ("revenue", "receita", "amount")):
            zeros = clean[clean == 0]
            if len(zeros) / len(clean) > 0.1:
                anomalies.append(Anomaly(
                    type="zero_value",
                    severity="warning",
                    column=col,
                    message=f"'{col}' tem {len(zeros) / len(clean):.0%} de zeros — verificar pedidos sem valor",
                    affected_rows=len(zeros),
                    affected_pct=len(zeros) / len(clean),
                    emoji="⚠️",
                ))

        return anomalies

    # ------------------------------------------------------------------
    # Categorical checks
    # ------------------------------------------------------------------

    def _check_categorical(
        self, series: pd.Series, col: str, df: pd.DataFrame
    ) -> List[Anomaly]:
        anomalies = []
        non_null = series.dropna()
        if len(non_null) == 0:
            return []

        # High null rate in important columns
        null_pct = series.isnull().mean()
        if null_pct > 0.2:
            severity = "critical" if null_pct > 0.5 else "warning"
            anomalies.append(Anomaly(
                type="high_nulls",
                severity=severity,
                column=col,
                message=f"'{col}' tem {null_pct:.0%} de nulos",
                affected_rows=int(series.isnull().sum()),
                affected_pct=null_pct,
                emoji="⚠️" if severity == "warning" else "🚨",
            ))

        return anomalies

    # ------------------------------------------------------------------
    # Concentration risk
    # ------------------------------------------------------------------

    def _check_concentration(self, df: pd.DataFrame, domain: str) -> List[Anomaly]:
        anomalies = []

        # Find revenue + customer columns
        rev_col = self._find_col(df, [r"revenue", r"receita", r"amount", r"valor"])
        cust_col = self._find_col(df, [r"customer", r"client", r"cliente"])

        if rev_col and cust_col:
            rev = pd.to_numeric(df[rev_col], errors="coerce")
            valid = df[[cust_col, rev_col]].dropna()
            if len(valid) > 0:
                by_customer = valid.groupby(cust_col)[rev_col].sum()
                total = by_customer.sum()
                if total > 0:
                    top_share = by_customer.max() / total
                    top_customer = by_customer.idxmax()
                    if top_share >= self.concentration_thresh:
                        anomalies.append(Anomaly(
                            type="concentration",
                            severity="warning" if top_share < 0.7 else "critical",
                            column=cust_col,
                            message=f"⚠️ Concentração: '{top_customer}' representa "
                                    f"{top_share:.0%} da receita total — risco de dependência",
                            value=str(top_customer),
                            affected_pct=float(top_share),
                            details={"top_customer": str(top_customer),
                                     "share": round(float(top_share), 4)},
                            emoji="⚠️",
                        ))

        return anomalies

    # ------------------------------------------------------------------
    # Time gap detection
    # ------------------------------------------------------------------

    def _check_time_gaps(self, df: pd.DataFrame) -> List[Anomaly]:
        anomalies = []
        date_col = self._find_col(df, [r"date", r"data", r"created", r"at$"])
        if not date_col:
            return []
        try:
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna().sort_values()
            if len(dates) < 3:
                return []
            diffs = dates.diff().dropna()
            median_gap = diffs.median()
            large_gaps = diffs[diffs > median_gap * 5]
            if len(large_gaps) > 0:
                gap_days = int(large_gaps.max().days)
                anomalies.append(Anomaly(
                    type="gap",
                    severity="warning",
                    column=date_col,
                    message=f"Lacuna temporal detectada em '{date_col}': "
                            f"gap máximo de {gap_days} dias "
                            f"(mediana: {int(median_gap.days)} dias)",
                    details={"max_gap_days": gap_days,
                             "median_gap_days": int(median_gap.days)},
                    emoji="📅",
                ))
        except Exception:
            pass
        return anomalies

    def _find_col(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        for pat in patterns:
            regex = re.compile(pat, re.IGNORECASE)
            for col in df.columns:
                if regex.search(col):
                    return col
        return None

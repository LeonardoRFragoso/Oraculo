"""
Sprint 2 — Data Quality Scorer

Computes a 0-100 composite quality score for any dataset, broken down
into four dimensions:

  Completeness   (30 pts) — absence of nulls
  Uniqueness     (25 pts) — absence of duplicates + ID uniqueness
  Consistency    (25 pts) — low cardinality anomalies, type consistency
  Validity       (20 pts) — outlier ratio, PII exposure, constant columns

Each dimension produces a sub-score and a list of findings.
The final report is designed to be shown directly in the UI.
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from catalog.profiler import DatasetProfile

logger = logging.getLogger(__name__)


@dataclass
class DimensionScore:
    name: str
    score: float          # 0-100 within this dimension
    weight: float         # contribution weight (0-1)
    weighted_score: float
    findings: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class QualityReport:
    dataset_name: str
    overall_score: float          # 0-100
    grade: str                    # A / B / C / D / F
    dimensions: List[DimensionScore] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    scored_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dimensions"] = [dim.to_dict() for dim in self.dimensions]
        return d


class DataQualityScorer:
    """
    Computes a quality score from a DatasetProfile.

    Usage:
        scorer = DataQualityScorer()
        report = scorer.score(profile)
        print(report.overall_score)   # 82.5
        print(report.grade)           # B
    """

    WEIGHTS = {
        "completeness": 0.30,
        "uniqueness":   0.25,
        "consistency":  0.25,
        "validity":     0.20,
    }

    def score(self, profile: DatasetProfile) -> QualityReport:
        dimensions = [
            self._score_completeness(profile),
            self._score_uniqueness(profile),
            self._score_consistency(profile),
            self._score_validity(profile),
        ]

        overall = sum(d.weighted_score for d in dimensions)
        overall = round(min(max(overall, 0), 100), 1)
        grade = self._to_grade(overall)

        critical = [f for d in dimensions for f in d.findings if "%" in f and self._is_critical(f)]
        recommendations = self._build_recommendations(profile, dimensions)

        logger.info(f"Quality score for '{profile.dataset_name}': {overall} ({grade})")

        return QualityReport(
            dataset_name=profile.dataset_name,
            overall_score=overall,
            grade=grade,
            dimensions=dimensions,
            critical_issues=critical,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # Dimension scorers
    # ------------------------------------------------------------------

    def _score_completeness(self, profile: DatasetProfile) -> DimensionScore:
        """30 pts — penalize for nulls at column and dataset level."""
        findings = []
        col_scores = []

        for col in profile.columns:
            col_scores.append(1.0 - col.null_pct)
            if col.null_pct > 0.3:
                findings.append(f"'{col.name}': {col.null_pct:.0%} nulls")

        avg_completeness = sum(col_scores) / max(len(col_scores), 1)
        raw = avg_completeness * 100

        weight = self.WEIGHTS["completeness"]
        return DimensionScore(
            name="completeness",
            score=round(raw, 1),
            weight=weight,
            weighted_score=round(raw * weight, 2),
            findings=findings,
        )

    def _score_uniqueness(self, profile: DatasetProfile) -> DimensionScore:
        """25 pts — penalize duplicate rows and ID columns with duplicates."""
        findings = []
        score = 100.0

        # Duplicate row penalty (up to -40 pts)
        if profile.duplicate_row_pct > 0:
            penalty = min(profile.duplicate_row_pct * 200, 40)
            score -= penalty
            findings.append(
                f"{profile.duplicate_row_count:,} duplicate rows "
                f"({profile.duplicate_row_pct:.1%})"
            )

        # ID-like columns with low uniqueness penalty
        for col in profile.columns:
            if col.is_id_like and col.unique_pct < 0.99:
                penalty = (1 - col.unique_pct) * 20
                score -= penalty
                findings.append(
                    f"ID column '{col.name}' has {col.unique_pct:.1%} uniqueness"
                )

        score = max(score, 0)
        weight = self.WEIGHTS["uniqueness"]
        return DimensionScore(
            name="uniqueness",
            score=round(score, 1),
            weight=weight,
            weighted_score=round(score * weight, 2),
            findings=findings,
        )

    def _score_consistency(self, profile: DatasetProfile) -> DimensionScore:
        """25 pts — penalize constant columns, very high / very low cardinality anomalies."""
        findings = []
        score = 100.0

        constant_cols = [c for c in profile.columns if c.is_constant]
        if constant_cols:
            penalty = min(len(constant_cols) * 5, 25)
            score -= penalty
            for col in constant_cols:
                findings.append(f"Column '{col.name}' has zero variance (constant)")

        # Columns with suspiciously low cardinality in a supposedly free-text field
        for col in profile.columns:
            if (col.col_type == "text" and col.unique_pct < 0.05
                    and col.total_count > 100):
                findings.append(
                    f"Text column '{col.name}' has very low cardinality "
                    f"({col.unique_count} unique / {col.total_count} rows)"
                )
                score -= 3

        score = max(score, 0)
        weight = self.WEIGHTS["consistency"]
        return DimensionScore(
            name="consistency",
            score=round(score, 1),
            weight=weight,
            weighted_score=round(score * weight, 2),
            findings=findings,
        )

    def _score_validity(self, profile: DatasetProfile) -> DimensionScore:
        """20 pts — penalize outliers, PII exposure, overall null rate."""
        findings = []
        score = 100.0

        # Outlier penalty
        high_outlier_cols = [c for c in profile.columns if c.outlier_pct > 0.05]
        for col in high_outlier_cols:
            penalty = min(col.outlier_pct * 50, 10)
            score -= penalty
            findings.append(
                f"Column '{col.name}': {col.outlier_pct:.1%} outliers detected"
            )

        # PII exposure warning (no score penalty, just finding)
        pii_cols = [c for c in profile.columns if c.is_pii]
        for col in pii_cols:
            findings.append(
                f"⚠️  Column '{col.name}' may contain {col.pii_type} (PII)"
            )

        # Global null penalty
        if profile.null_pct_overall > 0.2:
            penalty = min((profile.null_pct_overall - 0.2) * 50, 20)
            score -= penalty
            findings.append(
                f"Overall null rate: {profile.null_pct_overall:.1%}"
            )

        score = max(score, 0)
        weight = self.WEIGHTS["validity"]
        return DimensionScore(
            name="validity",
            score=round(score, 1),
            weight=weight,
            weighted_score=round(score * weight, 2),
            findings=findings,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_grade(self, score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 45:
            return "D"
        return "F"

    def _is_critical(self, finding: str) -> bool:
        """Heuristic: mark as critical if the pct in the finding is > 30%."""
        import re
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", finding)
        if match:
            return float(match.group(1)) > 30
        return False

    def _build_recommendations(
        self,
        profile: DatasetProfile,
        dimensions: List[DimensionScore],
    ) -> List[str]:
        recs = []
        dim_map = {d.name: d for d in dimensions}

        if dim_map["completeness"].score < 70:
            recs.append(
                "Fill or impute high-null columns before analysis — "
                "consider median/mode imputation or data re-extraction."
            )
        if dim_map["uniqueness"].score < 70:
            recs.append(
                "Deduplicate rows — check for ETL pipeline issues "
                "or missing dedup logic at ingestion."
            )
        if dim_map["consistency"].score < 70:
            recs.append(
                "Remove constant columns and validate categorical columns "
                "for encoding errors."
            )
        if dim_map["validity"].score < 70:
            recs.append(
                "Investigate outlier values — they may indicate data entry "
                "errors, unit mismatches or fraud signals."
            )
        pii_cols = [c.name for c in profile.columns if c.is_pii]
        if pii_cols:
            recs.append(
                f"PII detected in columns: {', '.join(pii_cols)}. "
                "Ensure LGPD/GDPR compliance — consider masking or tokenization."
            )
        if profile.duplicate_row_count > 0:
            recs.append(
                f"Remove {profile.duplicate_row_count:,} duplicate rows "
                "before training models or generating reports."
            )
        return recs

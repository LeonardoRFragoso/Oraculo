"""
Sprint 5 — Insight Engine (AI Data Analyst)

Orchestrates KPI generation + anomaly detection on all datasets
of a connected source, producing a complete AnalysisReport.

This is the "proactive intelligence" feature:
the user connects data → the system automatically generates insights
WITHOUT the user asking any questions.

LLM narrative synthesis is optional — graceful fallback to
rule-based text if Claude/OpenAI is unavailable.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from analyst.kpi_generator import KPI, KPIGenerator
from analyst.anomaly_detector import Anomaly, AnomalyDetector

logger = logging.getLogger(__name__)


@dataclass
class DatasetAnalysis:
    dataset_name: str
    domain: str
    row_count: int
    kpis: List[KPI] = field(default_factory=list)
    anomalies: List[Anomaly] = field(default_factory=list)
    summary: str = ""         # LLM or rule-based narrative

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "domain": self.domain,
            "row_count": self.row_count,
            "kpis": [k.to_dict() for k in self.kpis],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "summary": self.summary,
        }


@dataclass
class AnalysisReport:
    source_id: str
    source_name: str
    connector_type: str
    datasets: List[DatasetAnalysis] = field(default_factory=list)
    executive_summary: str = ""
    total_kpis: int = 0
    total_anomalies: int = 0
    critical_count: int = 0
    analyzed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "connector_type": self.connector_type,
            "analyzed_at": self.analyzed_at,
            "executive_summary": self.executive_summary,
            "total_kpis": self.total_kpis,
            "total_anomalies": self.total_anomalies,
            "critical_count": self.critical_count,
            "datasets": [d.to_dict() for d in self.datasets],
        }


class InsightEngine:
    """
    Proactive AI Data Analyst.

    Connects to a data source, loads data, and automatically generates:
      - Domain-aware KPIs
      - Anomaly alerts
      - Executive summary narrative

    Usage:
        engine = InsightEngine()
        report = engine.analyze(source_id="abc-123", record=registry_record)
        print(report.executive_summary)
    """

    def __init__(self, max_rows: int = 100_000):
        self.max_rows = max_rows
        self._kpi_gen = KPIGenerator()
        self._anomaly_det = AnomalyDetector()

    def analyze(self, source_id: str, record: Any) -> AnalysisReport:
        """Run full proactive analysis on a connected source."""
        logger.info(f"AI Analyst: analyzing '{record.name}' ({record.connector_type})")

        report = AnalysisReport(
            source_id=source_id,
            source_name=record.name,
            connector_type=record.connector_type,
        )

        try:
            import sys
            from pathlib import Path
            _root = str(Path(__file__).parent.parent)
            if _root not in sys.path:
                sys.path.insert(0, _root)

            from catalog.schema_discovery import SchemaDiscovery
            from catalog.registry import DataSourceRegistry

            disc = SchemaDiscovery()
            connector = disc._build_connector(record)
            if not connector.connect():
                report.executive_summary = "Não foi possível conectar à fonte de dados."
                return report

            result = connector.extract()
            connector.close()

            if not result.success or not result.dataframes:
                report.executive_summary = "Nenhum dado estruturado encontrado para análise."
                return report

            # Get domain info from stored datasets
            domain_map = {d["name"]: d.get("domain", "unknown") for d in record.datasets}

            for ds_name, df in result.dataframes.items():
                df = df.head(self.max_rows)
                domain = domain_map.get(ds_name, "unknown")

                kpis = self._kpi_gen.generate(df, domain=domain, source_name=ds_name)
                anomalies = self._anomaly_det.detect(df, domain=domain, source_name=ds_name)
                summary = self._build_dataset_summary(ds_name, domain, df, kpis, anomalies)

                report.datasets.append(DatasetAnalysis(
                    dataset_name=ds_name,
                    domain=domain,
                    row_count=len(df),
                    kpis=kpis,
                    anomalies=anomalies,
                    summary=summary,
                ))

            report.total_kpis = sum(len(d.kpis) for d in report.datasets)
            report.total_anomalies = sum(len(d.anomalies) for d in report.datasets)
            report.critical_count = sum(
                1 for d in report.datasets
                for a in d.anomalies if a.severity == "critical"
            )

            report.executive_summary = self._build_executive_summary(report)
            logger.info(
                f"✓ Analysis complete: {report.total_kpis} KPIs, "
                f"{report.total_anomalies} anomalies ({report.critical_count} critical)"
            )

        except Exception as e:
            logger.error(f"InsightEngine error: {e}", exc_info=True)
            report.executive_summary = f"Erro na análise: {e}"

        return report

    # ------------------------------------------------------------------
    # Narrative builders (zero LLM cost — rule-based)
    # ------------------------------------------------------------------

    def _build_dataset_summary(
        self,
        ds_name: str,
        domain: str,
        df: pd.DataFrame,
        kpis: List[KPI],
        anomalies: List[Anomaly],
    ) -> str:
        lines = [f"📊 Dataset '{ds_name}' — {len(df):,} registros | Domínio: {domain.upper()}"]

        # Top KPIs
        top_kpis = [k for k in kpis if k.unit in ("R$", "%", "clientes") and k.value is not None][:3]
        if top_kpis:
            kpi_texts = [
                f"{k.name}: {k.value:,.2f}{k.unit}" if isinstance(k.value, float)
                else f"{k.name}: {k.value} {k.unit}"
                for k in top_kpis
            ]
            lines.append("KPIs: " + " | ".join(kpi_texts))

        # Anomalies
        critical = [a for a in anomalies if a.severity == "critical"]
        warnings = [a for a in anomalies if a.severity == "warning"]
        if critical:
            lines.append(f"🚨 {len(critical)} alerta(s) crítico(s):")
            for a in critical[:3]:
                lines.append(f"   • {a.message}")
        if warnings:
            lines.append(f"⚠️ {len(warnings)} aviso(s):")
            for a in warnings[:2]:
                lines.append(f"   • {a.message}")

        return "\n".join(lines)

    def _build_executive_summary(self, report: AnalysisReport) -> str:
        lines = [
            f"🔮 Análise Automática — {report.source_name}",
            f"Fonte: {report.connector_type} | {len(report.datasets)} dataset(s) analisado(s)",
            "",
        ]

        for ds in report.datasets:
            lines.append(ds.summary)
            lines.append("")

        # Footer
        if report.critical_count > 0:
            lines.append(
                f"🚨 ATENÇÃO: {report.critical_count} anomalia(s) crítica(s) detectada(s). "
                "Revisão imediata recomendada."
            )
        elif report.total_anomalies > 0:
            lines.append(
                f"⚠️ {report.total_anomalies} aviso(s) detectado(s). Revisar os dados."
            )
        else:
            lines.append("✅ Nenhuma anomalia crítica detectada.")

        return "\n".join(lines)

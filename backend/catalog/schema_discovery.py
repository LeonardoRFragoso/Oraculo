"""
Schema Discovery — orchestrates connector → semantic classification → registry.

This is the main entry point for connecting a new data source:
    1. Instantiate the right connector from the registry config
    2. Run discover() to get DatasetInfo list
    3. Run SemanticEngine.classify_all() on discovered datasets
    4. Persist results to the registry
    5. Return a structured discovery report
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from connectors.base import ConnectorType, DatasetInfo
from catalog.semantic_engine import DomainClassification, SemanticEngine
from catalog.registry import DataSourceRecord, DataSourceRegistry
from catalog.profiler import DataProfiler, DatasetProfile
from catalog.quality_scorer import DataQualityScorer, QualityReport

_DOCUMENT_TYPES = {"pdf", "docx", "txt", "xml"}

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryReport:
    source_id: str
    source_name: str
    connector_type: str
    success: bool
    datasets: List[Dict] = field(default_factory=list)
    domain_summary: Dict[str, Any] = field(default_factory=dict)
    profiles: Dict[str, Dict] = field(default_factory=dict)       # dataset_name → DatasetProfile dict
    quality_scores: Dict[str, Dict] = field(default_factory=dict) # dataset_name → QualityReport dict
    quality_summary: Dict[str, Any] = field(default_factory=dict)
    domain_classifications: Dict[str, Dict] = field(default_factory=dict)
    total_tables: int = 0
    total_rows: int = 0
    error: Optional[str] = None


class SchemaDiscovery:
    """
    Orchestrator: connect → discover → classify → persist.
    """

    def __init__(
        self,
        registry: Optional[DataSourceRegistry] = None,
        semantic_engine: Optional[SemanticEngine] = None,
    ):
        self.registry = registry or DataSourceRegistry()
        self.semantic_engine = semantic_engine or SemanticEngine()
        self.profiler = DataProfiler()
        self.quality_scorer = DataQualityScorer()
        self._doc_indexer = None  # lazy — avoids circular import

    def discover(self, source_id: str) -> DiscoveryReport:
        """
        Run full discovery for a registered data source.
        Updates registry with discovered schema + domain classifications.
        """
        record = self.registry.get(source_id)
        if not record:
            return DiscoveryReport(
                source_id=source_id,
                source_name="unknown",
                connector_type="unknown",
                success=False,
                error=f"Source {source_id} not found in registry",
            )

        logger.info(f"Starting discovery for: {record.name} ({record.connector_type})")
        self.registry.update_status(source_id, "connecting")

        try:
            connector = self._build_connector(record)
            if not connector.connect():
                self.registry.update_status(source_id, "error", "Connection failed")
                return DiscoveryReport(
                    source_id=source_id,
                    source_name=record.name,
                    connector_type=record.connector_type,
                    success=False,
                    error="Connection failed — check credentials or file path",
                )

            datasets: List[DatasetInfo] = connector.discover()

            # Sprint 2: extract data for profiling (sample up to 50k rows)
            logger.info("Extracting data sample for profiling...")
            profiles: Dict[str, DatasetProfile] = {}
            quality_reports: Dict[str, QualityReport] = {}
            try:
                result = connector.extract()
                if result.success and result.dataframes:
                    for ds_name, df in result.dataframes.items():
                        sample_df = df.head(50_000)
                        profile = self.profiler.profile(sample_df, ds_name)
                        profiles[ds_name] = profile
                        quality_reports[ds_name] = self.quality_scorer.score(profile)
                        logger.info(
                            f"  [{ds_name}] quality: {quality_reports[ds_name].overall_score} "
                            f"({quality_reports[ds_name].grade})"
                        )
            except Exception as e:
                logger.warning(f"Profiling failed (non-critical): {e}")

            connector.close()

            if not datasets:
                self.registry.update_status(source_id, "error", "No datasets discovered")
                return DiscoveryReport(
                    source_id=source_id,
                    source_name=record.name,
                    connector_type=record.connector_type,
                    success=False,
                    error="No tables or datasets found in the source",
                )

            # Fase 0: classify domains
            logger.info(f"Classifying {len(datasets)} datasets with Semantic Engine...")
            classifications = self.semantic_engine.classify_all(datasets)

            # Serialize
            datasets_dicts = [ds.to_dict() for ds in datasets]
            domain_summary = self._build_domain_summary(datasets, classifications)
            domain_classifications = {
                name: {
                    "domain": cls.domain.value,
                    "confidence": cls.confidence,
                    "signals": cls.signals_found,
                }
                for name, cls in classifications.items()
            }

            profiles_dicts = {name: p.to_dict() for name, p in profiles.items()}
            quality_dicts = {name: r.to_dict() for name, r in quality_reports.items()}
            quality_summary = self._build_quality_summary(quality_reports)

            # Persist to registry (includes quality summary)
            enhanced_domain_summary = {**domain_summary, "quality": quality_summary}
            self.registry.update_datasets(source_id, datasets_dicts, enhanced_domain_summary)

            total_rows = sum(ds.row_count for ds in datasets)

            # Sprint 4: auto-index document sources into VectorStore
            chunks_indexed = 0
            if record.connector_type in _DOCUMENT_TYPES:
                try:
                    from rag.document_indexer import DocumentIndexer
                    if self._doc_indexer is None:
                        self._doc_indexer = DocumentIndexer()
                    idx_result = self._doc_indexer.index(source_id, record)
                    chunks_indexed = idx_result.chunks_indexed
                    if idx_result.success:
                        logger.info(
                            f"✓ Document indexed: {record.name} "
                            f"({chunks_indexed} chunks)"
                        )
                    else:
                        logger.warning(
                            f"Document indexing failed (non-critical): {idx_result.error}"
                        )
                except Exception as e:
                    logger.warning(f"Document indexing skipped: {e}")

            logger.info(
                f"Discovery complete: {record.name} — "
                f"{len(datasets)} tables, {total_rows:,} rows"
            )

            return DiscoveryReport(
                source_id=source_id,
                source_name=record.name,
                connector_type=record.connector_type,
                success=True,
                datasets=datasets_dicts,
                domain_summary=enhanced_domain_summary,
                domain_classifications=domain_classifications,
                profiles=profiles_dicts,
                quality_scores=quality_dicts,
                quality_summary=quality_summary,
                total_tables=len(datasets),
                total_rows=total_rows,
            )

        except Exception as e:
            logger.error(f"Discovery error for {record.name}: {e}", exc_info=True)
            self.registry.update_status(source_id, "error", str(e))
            return DiscoveryReport(
                source_id=source_id,
                source_name=record.name,
                connector_type=record.connector_type,
                success=False,
                error=str(e),
            )

    def _build_connector(self, record: DataSourceRecord):
        """Factory: instantiate the right connector from a registry record."""
        from connectors.files import (
            CSVConnector, ExcelConnector, JSONConnector,
            ParquetConnector, DocumentConnector,
        )
        from connectors.databases import (
            SQLiteConnector, PostgreSQLConnector, MySQLConnector,
        )

        ctype = ConnectorType(record.connector_type)
        config = record.config

        connector_map = {
            ConnectorType.CSV: CSVConnector,
            ConnectorType.EXCEL: ExcelConnector,
            ConnectorType.JSON: JSONConnector,
            ConnectorType.PARQUET: ParquetConnector,
            ConnectorType.PDF: DocumentConnector,
            ConnectorType.DOCX: DocumentConnector,
            ConnectorType.TXT: DocumentConnector,
            ConnectorType.XML: DocumentConnector,
            ConnectorType.SQLITE: SQLiteConnector,
            ConnectorType.POSTGRESQL: PostgreSQLConnector,
            ConnectorType.MYSQL: MySQLConnector,
        }

        cls = connector_map.get(ctype)
        if not cls:
            raise ValueError(f"No connector implemented for type: {ctype.value}")
        return cls(config)

    def _build_quality_summary(
        self, quality_reports: Dict[str, "QualityReport"]
    ) -> Dict[str, Any]:
        if not quality_reports:
            return {}
        scores = [r.overall_score for r in quality_reports.values()]
        avg_score = round(sum(scores) / len(scores), 1)
        from catalog.quality_scorer import DataQualityScorer
        scorer = DataQualityScorer()
        return {
            "average_score": avg_score,
            "overall_grade": scorer._to_grade(avg_score),
            "per_dataset": {
                name: {"score": r.overall_score, "grade": r.grade}
                for name, r in quality_reports.items()
            },
        }

    def _build_domain_summary(
        self,
        datasets: List[DatasetInfo],
        classifications: Dict[str, DomainClassification],
    ) -> Dict[str, Any]:
        domain_counts: Dict[str, int] = {}
        for name, cls in classifications.items():
            domain = cls.domain.value
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        primary_domain = max(domain_counts, key=domain_counts.get) if domain_counts else "unknown"

        return {
            "primary_domain": primary_domain,
            "domain_distribution": domain_counts,
            "total_tables": len(datasets),
            "total_rows": sum(ds.row_count for ds in datasets),
            "classified_tables": [
                {
                    "table": name,
                    "domain": cls.domain.value,
                    "confidence": cls.confidence,
                }
                for name, cls in sorted(
                    classifications.items(),
                    key=lambda x: x[1].confidence,
                    reverse=True,
                )
            ],
        }

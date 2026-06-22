"""
Data Source Registry — central catalog of all connected sources.

Persists to JSON for now (Sprint 2 migrates to PostgreSQL).
Each entry tracks connection config, discovered schemas, domain
classifications and connection status.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from connectors.base import ConnectorType, DataDomain

logger = logging.getLogger(__name__)


@dataclass
class DataSourceRecord:
    id: str
    name: str
    connector_type: str
    config: Dict[str, Any]           # connection params (passwords should be encrypted in prod)
    owner_id: str = "default"
    description: Optional[str] = None
    status: str = "registered"        # registered | connected | error | disconnected
    datasets: List[Dict] = field(default_factory=list)    # serialized DatasetInfo dicts
    domain_summary: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_sync_at: Optional[str] = None
    error_message: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Never expose passwords in API responses
        safe_config = {
            k: "***" if "password" in k.lower() or "secret" in k.lower() or "token" in k.lower()
            else v
            for k, v in self.config.items()
        }
        d["config"] = safe_config
        return d


class DataSourceRegistry:
    """
    In-memory + JSON-persisted registry of all data sources.

    Thread-safety note: this implementation is single-process safe.
    Sprint 7 (PostgreSQL migration) will add proper concurrency.
    """

    def __init__(self, storage_path: str = "../dados/catalog/registry.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._sources: Dict[str, DataSourceRecord] = {}
        self._load()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        connector_type: ConnectorType,
        config: Dict[str, Any],
        owner_id: str = "default",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> DataSourceRecord:
        """Register a new data source and return its record."""
        source_id = str(uuid.uuid4())
        record = DataSourceRecord(
            id=source_id,
            name=name,
            connector_type=connector_type.value,
            config=config,
            owner_id=owner_id,
            description=description,
            tags=tags or [],
        )
        self._sources[source_id] = record
        self._save()
        logger.info(f"Registered data source: {name} ({connector_type.value}) → {source_id}")
        return record

    def get(self, source_id: str) -> Optional[DataSourceRecord]:
        if source_id not in self._sources:
            self._load()
        return self._sources.get(source_id)

    def reload(self):
        """Reload from disk — keeps separate singleton instances in sync."""
        self._load()

    def list(self, owner_id: Optional[str] = None) -> List[DataSourceRecord]:
        self._load()   # always read from disk so all singletons stay in sync
        sources = list(self._sources.values())
        if owner_id:
            sources = [s for s in sources if s.owner_id == owner_id]
        return sorted(sources, key=lambda s: s.updated_at, reverse=True)

    def update_status(
        self,
        source_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[DataSourceRecord]:
        record = self._sources.get(source_id)
        if not record:
            return None
        record.status = status
        record.error_message = error_message
        record.updated_at = datetime.utcnow().isoformat()
        self._save()
        return record

    def update_datasets(
        self,
        source_id: str,
        datasets: List[Dict],
        domain_summary: Dict[str, Any],
    ) -> Optional[DataSourceRecord]:
        record = self._sources.get(source_id)
        if not record:
            return None
        record.datasets = datasets
        record.domain_summary = domain_summary
        record.last_sync_at = datetime.utcnow().isoformat()
        record.updated_at = datetime.utcnow().isoformat()
        record.status = "connected"
        self._save()
        return record

    def delete(self, source_id: str) -> bool:
        if source_id in self._sources:
            del self._sources[source_id]
            self._save()
            logger.info(f"Deleted data source: {source_id}")
            return True
        return False

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    def get_domain_summary(self, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Return aggregated domain distribution across all sources."""
        sources = self.list(owner_id=owner_id)
        domain_counts: Dict[str, int] = {}
        total_tables = 0
        total_rows = 0

        for source in sources:
            for dataset in source.datasets:
                domain = dataset.get("domain", DataDomain.UNKNOWN.value)
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                total_tables += 1
                total_rows += dataset.get("row_count", 0)

        return {
            "total_sources": len(sources),
            "total_tables": total_tables,
            "total_rows": total_rows,
            "domains": domain_counts,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self):
        try:
            data = {sid: asdict(record) for sid, record in self._sources.items()}
            self.storage_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Registry save error: {e}")

    def _load(self):
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self._sources = {
                    sid: DataSourceRecord(**record)
                    for sid, record in data.items()
                }
                logger.info(f"Registry loaded: {len(self._sources)} sources")
        except Exception as e:
            logger.error(f"Registry load error: {e}")
            self._sources = {}

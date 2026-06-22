"""
Sprint 7 — Graph Store

Builds and persists per-source Knowledge Graphs to disk.
Orchestrates EntityExtractor + RelationBuilder + KnowledgeGraph.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from graph.entity_extractor import EntityExtractor
from graph.relation_builder import RelationBuilder
from graph.knowledge_graph import KnowledgeGraph, GraphStats

logger = logging.getLogger(__name__)


class GraphStore:
    """
    Builds, persists, and loads per-source Knowledge Graphs.

    Usage:
        store = GraphStore()
        kg = store.build(source_id, record)        # build from source
        kg = store.load(source_id)                 # load from disk
        store.delete(source_id)                    # remove
    """

    def __init__(self, storage_root: str = "../dados/graphs"):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._extractor = EntityExtractor()
        self._builder = RelationBuilder()

    def build(self, source_id: str, record: Any) -> KnowledgeGraph:
        """
        Build a KnowledgeGraph from a connected data source.
        Automatically extracts entities and relations from all datasets.
        """
        import sys
        _root = str(Path(__file__).parent.parent)
        if _root not in sys.path:
            sys.path.insert(0, _root)

        from catalog.schema_discovery import SchemaDiscovery

        logger.info(f"Building knowledge graph for '{record.name}'")
        kg = KnowledgeGraph()

        try:
            disc = SchemaDiscovery()
            connector = disc._build_connector(record)
            if not connector.connect():
                logger.error(f"Could not connect to '{record.name}'")
                return kg

            result = connector.extract()
            connector.close()

            if not result.success or not result.dataframes:
                logger.warning(f"No structured data in '{record.name}'")
                return kg

            domain_map = {d["name"]: d.get("domain", "unknown") for d in record.datasets}

            all_entities = []
            all_relations = []

            for ds_name, df in result.dataframes.items():
                df = df.head(50_000)

                entities = self._extractor.extract(df, dataset_name=ds_name)
                relations = self._builder.build(df, entities, dataset_name=ds_name)

                all_entities.extend(entities)
                all_relations.extend(relations)

            kg.add_entities(all_entities)
            kg.add_relations(all_relations)

            stats = kg.compute_stats()
            logger.info(
                f"✓ Graph built: {stats.node_count} nodes, "
                f"{stats.edge_count} edges — '{record.name}'"
            )

            self._save(source_id, kg)

        except Exception as e:
            logger.error(f"Graph build error: {e}", exc_info=True)

        return kg

    def load(self, source_id: str) -> Optional[KnowledgeGraph]:
        path = self._graph_path(source_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return KnowledgeGraph.from_dict(data)
        except Exception as e:
            logger.error(f"Graph load error for {source_id}: {e}")
            return None

    def has_graph(self, source_id: str) -> bool:
        return self._graph_path(source_id).exists()

    def delete(self, source_id: str) -> bool:
        path = self._graph_path(source_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def _save(self, source_id: str, kg: KnowledgeGraph) -> None:
        path = self._graph_path(source_id)
        data = kg.to_dict()
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        logger.debug(f"Graph saved: {path}")

    def _graph_path(self, source_id: str) -> Path:
        return self.storage_root / f"{source_id}.json"

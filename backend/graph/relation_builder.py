"""
Sprint 7 — Relation Builder

Infers typed relationships between entity pairs from a DataFrame.

Relation types:
  PURCHASED        → CUSTOMER → PRODUCT (row co-occurrence)
  SOLD_BY          → PRODUCT → EMPLOYEE (row co-occurrence)
  LOCATED_IN       → CUSTOMER/EMPLOYEE → LOCATION
  BELONGS_TO       → PRODUCT/EMPLOYEE → CATEGORY/DEPARTMENT
  CORRELATED_WITH  → any pair with strong numeric correlation
  SAME_STATUS      → entities sharing the same STATUS value

Weight = (co-occurrence count) / (total rows)  → 0..1
"""

import logging
import re
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from graph.entity_extractor import Entity

logger = logging.getLogger(__name__)

# Predefined semantic relation pairs: (type_A, type_B) → relation_label
_SEMANTIC_PAIRS: Dict[Tuple[str, str], str] = {
    ("CUSTOMER", "PRODUCT"):    "PURCHASED",
    ("PRODUCT", "CUSTOMER"):    "PURCHASED_BY",
    ("PRODUCT", "EMPLOYEE"):    "SOLD_BY",
    ("EMPLOYEE", "PRODUCT"):    "SOLD",
    ("CUSTOMER", "LOCATION"):   "LOCATED_IN",
    ("EMPLOYEE", "LOCATION"):   "BASED_IN",
    ("EMPLOYEE", "DEPARTMENT"): "WORKS_IN",
    ("PRODUCT", "CATEGORY"):    "BELONGS_TO",
    ("CUSTOMER", "STATUS"):     "HAS_STATUS",
    ("PRODUCT", "BRAND"):       "MADE_BY",
}

# Minimum co-occurrence ratio to create a relation
_MIN_COOCCURRENCE = 0.05


@dataclass
class Relation:
    from_id: str
    to_id: str
    type: str
    weight: float = 1.0            # 0..1 — higher = stronger association
    count: int = 1                 # raw co-occurrence count
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "type": self.type,
            "weight": round(self.weight, 4),
            "count": self.count,
            "properties": self.properties,
        }


class RelationBuilder:
    """
    Builds typed relations between extracted entities.

    Usage:
        builder = RelationBuilder()
        relations = builder.build(df, entities, dataset_name="vendas")
    """

    def __init__(self, max_relations_per_col_pair: int = 500):
        self.max_relations = max_relations_per_col_pair

    def build(
        self,
        df: pd.DataFrame,
        entities: List[Entity],
        dataset_name: str = "dataset",
    ) -> List[Relation]:
        relations: List[Relation] = []
        n_rows = len(df)
        if n_rows == 0:
            return []

        # Index entities by (column, value) for fast lookup
        entity_by_col_val: Dict[Tuple[str, str], Entity] = {
            (e.source_column, e.label): e
            for e in entities
        }

        # Group entity columns by type
        col_type_map: Dict[str, str] = {e.source_column: e.type for e in entities}
        typed_cols: Dict[str, List[str]] = {}
        for col, etype in col_type_map.items():
            typed_cols.setdefault(etype, []).append(col)

        # Build relations for every pair of entity-type columns
        entity_cols = list(col_type_map.keys())
        processed_pairs = set()

        for col_a, col_b in combinations(entity_cols, 2):
            if (col_a, col_b) in processed_pairs:
                continue
            processed_pairs.add((col_a, col_b))
            processed_pairs.add((col_b, col_a))

            type_a = col_type_map[col_a]
            type_b = col_type_map[col_b]
            rel_type = (
                _SEMANTIC_PAIRS.get((type_a, type_b))
                or _SEMANTIC_PAIRS.get((type_b, type_a))
                or f"{type_a}_WITH_{type_b}"
            )

            col_relations = self._build_cooccurrence(
                df, col_a, col_b, rel_type, entity_by_col_val, n_rows
            )
            relations.extend(col_relations)

        logger.info(
            f"Built {len(relations)} relations from '{dataset_name}'"
        )
        return relations

    def _build_cooccurrence(
        self,
        df: pd.DataFrame,
        col_a: str,
        col_b: str,
        rel_type: str,
        entity_by_col_val: Dict[Tuple[str, str], Entity],
        n_rows: int,
    ) -> List[Relation]:
        relations = []
        try:
            # Drop rows where either col is null
            sub = df[[col_a, col_b]].dropna()
            if len(sub) == 0:
                return []

            # Count co-occurrences
            cooc = sub.groupby([col_a, col_b]).size().reset_index(name="count")

            # Filter low co-occurrence
            min_count = max(1, int(n_rows * _MIN_COOCCURRENCE))
            cooc = cooc[cooc["count"] >= min_count]

            if len(cooc) > self.max_relations:
                cooc = cooc.nlargest(self.max_relations, "count")

            for _, row in cooc.iterrows():
                val_a = str(row[col_a]).strip()
                val_b = str(row[col_b]).strip()
                count = int(row["count"])

                entity_a = entity_by_col_val.get((col_a, val_a))
                entity_b = entity_by_col_val.get((col_b, val_b))
                if entity_a is None or entity_b is None:
                    continue

                weight = count / n_rows
                relations.append(Relation(
                    from_id=entity_a.id,
                    to_id=entity_b.id,
                    type=rel_type,
                    weight=round(weight, 4),
                    count=count,
                ))

        except Exception as e:
            logger.warning(f"Relation building failed for {col_a}↔{col_b}: {e}")

        return relations

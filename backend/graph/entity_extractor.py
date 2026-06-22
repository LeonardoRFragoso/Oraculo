"""
Sprint 7 — Entity Extractor

Detects typed entities from DataFrames based on column semantics.

Entity types:
  CUSTOMER    → customer_name, client, empresa
  PRODUCT     → product, produto, sku, item
  EMPLOYEE    → employee, funcionario, pessoa
  LOCATION    → city, cidade, country, estado, regiao
  CATEGORY    → any low-cardinality categorical (<50 unique values)
  DATE        → date columns — grouped into MONTH/QUARTER buckets
  VALUE       → numeric buckets (low/medium/high)

Each unique value in a typed column becomes one Entity node.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Max cardinality for a column to be treated as categorical entities
_MAX_ENTITY_CARDINALITY = 200

# Column pattern → entity type
_PATTERNS = [
    (r"customer|client|empresa|cliente|compan",     "CUSTOMER"),
    (r"product|produto|item|sku|servico|service",   "PRODUCT"),
    (r"employee|funcionario|vendedor|seller|user",  "EMPLOYEE"),
    (r"city|cidade|country|pais|estado|state|region|regiao|uf\b", "LOCATION"),
    (r"category|categoria|tipo|type|segment|segmento|grupo|group", "CATEGORY"),
    (r"status|estado|situacao|phase|fase|stage",    "STATUS"),
    (r"department|depto|area|setor|division",       "DEPARTMENT"),
    (r"brand|marca|fabricante|manufacturer",        "BRAND"),
]


@dataclass
class Entity:
    id: str                          # unique within the graph: "<col_type>:<value>"
    type: str                        # CUSTOMER, PRODUCT, EMPLOYEE, …
    label: str                       # display name
    source_column: str               # original column name
    dataset: str                     # which dataset it came from
    properties: Dict[str, Any] = field(default_factory=dict)
    frequency: int = 1               # how many rows reference this entity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "source_column": self.source_column,
            "dataset": self.dataset,
            "properties": self.properties,
            "frequency": self.frequency,
        }


class EntityExtractor:
    """
    Extracts entity nodes from a DataFrame.

    Usage:
        extractor = EntityExtractor()
        entities = extractor.extract(df, dataset_name="vendas")
    """

    def extract(
        self,
        df: pd.DataFrame,
        dataset_name: str = "dataset",
        numeric_context: Optional[Dict[str, Any]] = None,
    ) -> List[Entity]:
        entities: List[Entity] = []
        seen_ids: Set[str] = set()

        for col in df.columns:
            etype = self._classify_column(col, df[col])
            if etype is None:
                continue

            col_entities = self._extract_column_entities(
                df, col, etype, dataset_name, seen_ids
            )
            entities.extend(col_entities)

        logger.info(
            f"Extracted {len(entities)} entities from '{dataset_name}' "
            f"({len(set(e.type for e in entities))} types)"
        )
        return entities

    # ------------------------------------------------------------------
    # Column classification
    # ------------------------------------------------------------------

    def _classify_column(self, col: str, series: pd.Series) -> Optional[str]:
        col_lower = col.lower()

        # Match known patterns
        for pattern, etype in _PATTERNS:
            if re.search(pattern, col_lower):
                # Confirm it's categorical
                nunique = series.nunique()
                if nunique < 1:
                    return None
                if nunique > _MAX_ENTITY_CARDINALITY:
                    return None
                return etype

        # Generic: low-cardinality object column → CATEGORY
        if series.dtype == object:
            nunique = series.nunique()
            if 2 <= nunique <= 30:
                return "CATEGORY"

        return None

    # ------------------------------------------------------------------
    # Entity extraction per column
    # ------------------------------------------------------------------

    def _extract_column_entities(
        self,
        df: pd.DataFrame,
        col: str,
        etype: str,
        dataset: str,
        seen_ids: Set[str],
    ) -> List[Entity]:
        entities = []
        value_counts = df[col].value_counts(dropna=True)

        # Find numeric columns to attach as properties (e.g. revenue per customer)
        numeric_cols = [
            c for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c]) and c != col
        ]

        for value, count in value_counts.items():
            label = str(value).strip()
            if not label or label.lower() in ("nan", "none", ""):
                continue

            entity_id = f"{etype}:{label}"
            if entity_id in seen_ids:
                # Update frequency if already added (cross-dataset dedup)
                continue
            seen_ids.add(entity_id)

            # Build properties from numeric columns aggregated for this entity
            props: Dict[str, Any] = {}
            mask = df[col] == value
            for num_col in numeric_cols[:4]:  # limit to 4 numeric props
                try:
                    vals = pd.to_numeric(df.loc[mask, num_col], errors="coerce").dropna()
                    if len(vals) > 0:
                        props[f"{num_col}_sum"]  = round(float(vals.sum()), 2)
                        props[f"{num_col}_mean"] = round(float(vals.mean()), 2)
                except Exception:
                    pass

            entities.append(Entity(
                id=entity_id,
                type=etype,
                label=label,
                source_column=col,
                dataset=dataset,
                properties=props,
                frequency=int(count),
            ))

        return entities

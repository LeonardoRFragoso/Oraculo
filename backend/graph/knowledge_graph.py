"""
Sprint 7 — Knowledge Graph

NetworkX-based graph with typed entities and weighted relations.
Provides graph analytics: centrality, communities, shortest paths,
neighbor queries, and entity search.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from graph.entity_extractor import Entity
from graph.relation_builder import Relation

logger = logging.getLogger(__name__)


@dataclass
class GraphStats:
    node_count: int = 0
    edge_count: int = 0
    entity_types: Dict[str, int] = field(default_factory=dict)
    relation_types: Dict[str, int] = field(default_factory=dict)
    density: float = 0.0
    avg_degree: float = 0.0
    top_entities: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
            "relation_types": self.relation_types,
            "density": round(self.density, 4),
            "avg_degree": round(self.avg_degree, 2),
            "top_entities": self.top_entities,
        }


class KnowledgeGraph:
    """
    In-memory knowledge graph powered by NetworkX.

    Usage:
        kg = KnowledgeGraph()
        kg.add_entities(entities)
        kg.add_relations(relations)
        neighbors = kg.neighbors("CUSTOMER:Michelin", depth=2)
        stats = kg.compute_stats()
    """

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def add_entities(self, entities: List[Entity]) -> None:
        for e in entities:
            self._g.add_node(
                e.id,
                type=e.type,
                label=e.label,
                source_column=e.source_column,
                dataset=e.dataset,
                frequency=e.frequency,
                **e.properties,
            )

    def add_relations(self, relations: List[Relation]) -> None:
        for r in relations:
            if not self._g.has_node(r.from_id) or not self._g.has_node(r.to_id):
                continue
            self._g.add_edge(
                r.from_id,
                r.to_id,
                type=r.type,
                weight=r.weight,
                count=r.count,
                **r.properties,
            )

    def clear(self) -> None:
        self._g.clear()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def neighbors(
        self,
        entity_id: str,
        depth: int = 1,
        relation_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return neighbors within `depth` hops."""
        if entity_id not in self._g:
            return []

        visited: Set[str] = set()
        result = []
        frontier = {entity_id}

        for hop in range(depth):
            next_frontier = set()
            for node in frontier:
                for neighbor in list(self._g.successors(node)) + list(self._g.predecessors(node)):
                    if neighbor in visited or neighbor == entity_id:
                        continue
                    edge_data = (
                        self._g.get_edge_data(node, neighbor)
                        or self._g.get_edge_data(neighbor, node)
                        or {}
                    )
                    if relation_type and edge_data.get("type") != relation_type:
                        continue
                    result.append({
                        "id": neighbor,
                        "hop": hop + 1,
                        "relation": edge_data.get("type", "RELATED"),
                        "weight": edge_data.get("weight", 1.0),
                        **{k: v for k, v in self._g.nodes[neighbor].items()},
                    })
                    visited.add(neighbor)
                    next_frontier.add(neighbor)
            frontier = next_frontier
            if not frontier:
                break

        return sorted(result, key=lambda x: (-x["weight"], x["hop"]))

    def shortest_path(
        self, from_id: str, to_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Find shortest path between two entities."""
        try:
            path = nx.shortest_path(self._g.to_undirected(), from_id, to_id)
            result = []
            for i, node in enumerate(path):
                node_data = dict(self._g.nodes[node])
                step: Dict[str, Any] = {"id": node, "step": i, **node_data}
                if i > 0:
                    edge = (
                        self._g.get_edge_data(path[i - 1], node)
                        or self._g.get_edge_data(node, path[i - 1])
                        or {}
                    )
                    step["via_relation"] = edge.get("type", "RELATED")
                result.append(step)
            return result
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search over entity labels."""
        query_lower = query.lower()
        results = []
        for node_id, data in self._g.nodes(data=True):
            label = str(data.get("label", "")).lower()
            if query_lower in label or query_lower in node_id.lower():
                degree = self._g.degree(node_id)
                results.append({
                    "id": node_id,
                    "degree": degree,
                    **data,
                })
        results.sort(key=lambda x: -x["degree"])
        return results[:limit]

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if entity_id not in self._g:
            return None
        data = dict(self._g.nodes[entity_id])
        edges_out = [
            {
                "to": v,
                "type": d.get("type"),
                "weight": d.get("weight"),
            }
            for _, v, d in self._g.out_edges(entity_id, data=True)
        ]
        edges_in = [
            {
                "from": u,
                "type": d.get("type"),
                "weight": d.get("weight"),
            }
            for u, _, d in self._g.in_edges(entity_id, data=True)
        ]
        return {
            "id": entity_id,
            **data,
            "edges_out": edges_out,
            "edges_in": edges_in,
            "degree": self._g.degree(entity_id),
        }

    def subgraph(
        self,
        entity_ids: List[str],
        include_neighbors: bool = True,
    ) -> Dict[str, Any]:
        """Return a subgraph as a vis.js / D3-ready dict."""
        nodes_set = set(entity_ids)
        if include_neighbors:
            for eid in entity_ids:
                nodes_set.update(self._g.successors(eid))
                nodes_set.update(self._g.predecessors(eid))

        sub = self._g.subgraph(nodes_set)
        return self._to_graph_dict(sub)

    def get_full_graph(self, max_nodes: int = 300) -> Dict[str, Any]:
        """Return the full graph (capped at max_nodes by degree)."""
        if self._g.number_of_nodes() <= max_nodes:
            return self._to_graph_dict(self._g)
        # Take top nodes by degree
        top_nodes = sorted(
            self._g.nodes(), key=lambda n: self._g.degree(n), reverse=True
        )[:max_nodes]
        sub = self._g.subgraph(top_nodes)
        return self._to_graph_dict(sub)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def compute_stats(self) -> GraphStats:
        g = self._g
        n = g.number_of_nodes()
        e = g.number_of_edges()

        entity_types: Dict[str, int] = {}
        for _, data in g.nodes(data=True):
            t = data.get("type", "UNKNOWN")
            entity_types[t] = entity_types.get(t, 0) + 1

        relation_types: Dict[str, int] = {}
        for _, _, data in g.edges(data=True):
            t = data.get("type", "RELATED")
            relation_types[t] = relation_types.get(t, 0) + 1

        density = nx.density(g) if n > 1 else 0.0
        avg_degree = (2 * e / n) if n > 0 else 0.0

        # Top entities by degree (most connected)
        degree_sorted = sorted(g.degree(), key=lambda x: x[1], reverse=True)[:10]
        top_entities = [
            {
                "id": nid,
                "degree": deg,
                "label": g.nodes[nid].get("label", nid),
                "type": g.nodes[nid].get("type", "?"),
            }
            for nid, deg in degree_sorted
        ]

        return GraphStats(
            node_count=n,
            edge_count=e,
            entity_types=entity_types,
            relation_types=relation_types,
            density=density,
            avg_degree=avg_degree,
            top_entities=top_entities,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {"id": nid, **dict(data)}
                for nid, data in self._g.nodes(data=True)
            ],
            "edges": [
                {"from": u, "to": v, **dict(data)}
                for u, v, data in self._g.edges(data=True)
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeGraph":
        kg = cls()
        for node in data.get("nodes", []):
            node_id = node.pop("id")
            kg._g.add_node(node_id, **node)
        for edge in data.get("edges", []):
            from_id = edge.pop("from")
            to_id = edge.pop("to")
            kg._g.add_edge(from_id, to_id, **edge)
        return kg

    def _to_graph_dict(self, g: nx.DiGraph) -> Dict[str, Any]:
        _TYPE_COLORS = {
            "CUSTOMER": "#4F81BD",
            "PRODUCT": "#C0504D",
            "EMPLOYEE": "#9BBB59",
            "LOCATION": "#F79646",
            "CATEGORY": "#8064A2",
            "STATUS": "#4BACC6",
            "DEPARTMENT": "#F2AB27",
            "BRAND": "#D24726",
        }
        nodes = []
        for nid, data in g.nodes(data=True):
            etype = data.get("type", "UNKNOWN")
            nodes.append({
                "id": nid,
                "label": data.get("label", nid),
                "type": etype,
                "color": _TYPE_COLORS.get(etype, "#888888"),
                "size": min(30, max(8, g.degree(nid) * 2)),
                "frequency": data.get("frequency", 1),
                **{k: v for k, v in data.items()
                   if k not in ("label", "type", "frequency")},
            })
        edges = []
        for u, v, data in g.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "type": data.get("type", "RELATED"),
                "weight": data.get("weight", 1.0),
                "count": data.get("count", 1),
            })
        return {"nodes": nodes, "edges": edges}

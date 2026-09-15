"""ShadowTrace — NetworkX actor correlation graph.

Design-doc §2.2 & PRD §4.2:
  - Cross-platform actor network graph
  - Nodes: actors (id, handle, platform, archetype, metadata)
  - Edges: co-posting, referral, transaction co-occurrence, shared credentials
  - Export: Cytoscape JSON and GraphML
"""

from __future__ import annotations

import io
import json
import logging
import uuid
from typing import Any, Optional

import networkx as nx

logger = logging.getLogger(__name__)

# Global NetworkX directed multigraph / graph
_actor_graph: nx.DiGraph = nx.DiGraph()


def get_actor_graph() -> nx.DiGraph:
    """Return the global NetworkX actor graph."""
    global _actor_graph
    return _actor_graph


def reset_actor_graph() -> None:
    """Clear all nodes and edges from the actor graph."""
    global _actor_graph
    _actor_graph.clear()


def add_actor_node(
    actor_id: str,
    handle: str,
    platform: str,
    archetype: str = "unknown",
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Add or update an actor node in the graph."""
    attrs = {
        "id": actor_id,
        "label": handle or actor_id,
        "handle": handle,
        "platform": platform,
        "archetype": archetype,
        "node_type": "actor",
    }
    if metadata:
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                attrs[k] = v
            else:
                attrs[k] = json.dumps(v)
    _actor_graph.add_node(actor_id, **attrs)


def add_actor_edge(
    src_id: str,
    dst_id: str,
    edge_type: str = "co_posting",
    weight: float = 1.0,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Add or update an edge between two actors."""
    attrs = {
        "edge_type": edge_type,
        "weight": float(weight),
    }
    if metadata:
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                attrs[k] = v
            else:
                attrs[k] = json.dumps(v)
    _actor_graph.add_edge(src_id, dst_id, **attrs)


def get_actor_neighbors(actor_id: str) -> list[dict[str, Any]]:
    """Return in and out neighbors of an actor."""
    if not _actor_graph.has_node(actor_id):
        return []

    results = []
    # Successors (out-edges)
    for neighbor in _actor_graph.successors(actor_id):
        edge_data = _actor_graph.get_edge_data(actor_id, neighbor) or {}
        node_data = _actor_graph.nodes[neighbor]
        results.append({
            "direction": "out",
            "actor_id": neighbor,
            "handle": node_data.get("handle", ""),
            "platform": node_data.get("platform", ""),
            "edge_type": edge_data.get("edge_type", "linked"),
            "weight": edge_data.get("weight", 1.0),
        })

    # Predecessors (in-edges)
    for neighbor in _actor_graph.predecessors(actor_id):
        if neighbor in [r["actor_id"] for r in results]:
            continue
        edge_data = _actor_graph.get_edge_data(neighbor, actor_id) or {}
        node_data = _actor_graph.nodes[neighbor]
        results.append({
            "direction": "in",
            "actor_id": neighbor,
            "handle": node_data.get("handle", ""),
            "platform": node_data.get("platform", ""),
            "edge_type": edge_data.get("edge_type", "linked"),
            "weight": edge_data.get("weight", 1.0),
        })

    return results


def export_cytoscape_json() -> dict[str, Any]:
    """Export the actor graph as Cytoscape JSON structure."""
    nodes = []
    edges = []

    for node_id, data in _actor_graph.nodes(data=True):
        node_dict = {"id": str(node_id), "label": data.get("handle", str(node_id))}
        for k, v in data.items():
            node_dict[k] = v
        nodes.append({"data": node_dict})

    edge_counter = 0
    for u, v, data in _actor_graph.edges(data=True):
        edge_id = f"e_{u}_{v}_{edge_counter}"
        edge_counter += 1
        edge_dict = {
            "id": edge_id,
            "source": str(u),
            "target": str(v),
            "edge_type": data.get("edge_type", "linked"),
            "weight": data.get("weight", 1.0),
        }
        for k, val in data.items():
            if k not in edge_dict:
                edge_dict[k] = val
        edges.append({"data": edge_dict})

    return {
        "nodes": nodes,
        "edges": edges,
        "elements": {
            "nodes": nodes,
            "edges": edges,
        },
        "stats": {
            "node_count": _actor_graph.number_of_nodes(),
            "edge_count": _actor_graph.number_of_edges(),
        },
    }


def export_graphml() -> str:
    """Export the actor graph as GraphML XML string."""
    try:
        import numpy as np
        if not hasattr(np, "float_"):
            np.float_ = np.float64  # type: ignore
        if not hasattr(np, "int_"):
            np.int_ = np.int64  # type: ignore
    except ImportError:
        pass

    stream = io.BytesIO()
    nx.write_graphml(_actor_graph, stream)
    return stream.getvalue().decode("utf-8")

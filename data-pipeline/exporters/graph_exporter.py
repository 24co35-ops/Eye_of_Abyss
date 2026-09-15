"""Unified actor graph exporter (GraphML format)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import networkx as nx

from shared.schemas import CriminalActorProfile


def export_actor_graph(
    actors: List[CriminalActorProfile],
    transactions: List[Dict[str, any]],
    output_dir: str = "./output",
) -> Path:
    """
    Exports unified NetworkX graph into:
      - output/shared/actor_graph.graphml
    """
    shared_dir = Path(output_dir) / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)

    g = nx.DiGraph()

    for actor in actors:
        aid = str(actor.actor_id)
        handle = actor.handles[0] if actor.handles else aid
        
        # Actor node
        g.add_node(
            f"actor_{aid}",
            label=handle,
            node_type="actor",
            archetype=actor.archetype,
            timezone=actor.timezone,
            data_source="synthetic",
        )

        # Platforms
        for plat in actor.platforms:
            plat_id = f"plat_{plat.lower()}"
            if not g.has_node(plat_id):
                g.add_node(plat_id, label=plat, node_type="platform", data_source="synthetic")
            g.add_edge(f"actor_{aid}", plat_id, relationship="POSTED_ON")

        # Wallets
        for wallet in actor.wallet_addresses:
            w_id = f"wallet_{wallet}"
            if not g.has_node(w_id):
                g.add_node(w_id, label=wallet, node_type="wallet", data_source="synthetic")
            g.add_edge(f"actor_{aid}", w_id, relationship="OPERATES_WALLET")

    # Transaction edges
    for tx in transactions:
        from_w = f"wallet_{tx.get('from_address')}"
        to_w = f"wallet_{tx.get('to_address')}"

        if not g.has_node(from_w):
            g.add_node(from_w, label=tx.get("from_address", ""), node_type="wallet", data_source="synthetic")
        if not g.has_node(to_w):
            g.add_node(to_w, label=tx.get("to_address", ""), node_type="wallet", data_source="synthetic")

        g.add_edge(
            from_w,
            to_w,
            relationship="TRANSACTED_WITH",
            tx_hash=tx.get("tx_hash", ""),
            amount_usd=float(tx.get("amount_usd", 0.0)),
            token=tx.get("token", ""),
            timestamp=tx.get("timestamp", ""),
            data_source="synthetic",
        )

        # VASP association if present
        vasp = tx.get("vasp_attribution")
        if vasp:
            vasp_id = f"vasp_{vasp.replace(' ', '_').lower()}"
            if not g.has_node(vasp_id):
                g.add_node(vasp_id, label=vasp, node_type="vasp", data_source="synthetic")
            g.add_edge(to_w, vasp_id, relationship="DEPOSITED_TO")

    try:
        import numpy as np
        if not hasattr(np, "float_"):
            np.float_ = np.float64  # type: ignore
        if not hasattr(np, "int_"):
            np.int_ = np.int64  # type: ignore
    except ImportError:
        pass

    graphml_path = shared_dir / "actor_graph.graphml"
    nx.write_graphml(g, graphml_path)

    return graphml_path

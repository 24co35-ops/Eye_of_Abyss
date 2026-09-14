"""
NetworkX Graph Builder and Cytoscape JSON visualization serializer.
Constructs directed transaction graph with centrality metrics, clustering labels, and forensic metadata.
"""

from __future__ import annotations

import networkx as nx
from typing import Any, Sequence

from services.chaineye.attribution.vasp_registry import get_vasp_attribution
from services.chaineye.graph.clustering import WalletCluster, cluster_wallet_network
from services.chaineye.graph.explorer import TransactionRecord


def build_transaction_graph(
    root_address: str, transactions: Sequence[TransactionRecord]
) -> tuple[nx.DiGraph, dict[str, WalletCluster]]:
    """
    Constructs a NetworkX directed multi-graph from transaction records and clusters.
    Computes degree centrality, flow volume, and risk attributes.
    """
    G = nx.DiGraph()
    clusters = cluster_wallet_network(root_address, transactions)

    # Reverse lookup address -> cluster
    addr_to_cluster: dict[str, WalletCluster] = {}
    for c in clusters.values():
        for a in c.addresses:
            addr_to_cluster[a] = c

    # Add nodes
    all_addresses = {root_address}
    for tx in transactions:
        all_addresses.add(tx.from_address)
        all_addresses.add(tx.to_address)

    for addr in all_addresses:
        cluster = addr_to_cluster.get(addr)
        vasp = get_vasp_attribution(addr)
        is_root = (addr.lower() == root_address.lower())

        label = vasp.name if vasp else (f"{addr[:6]}...{addr[-4:]}" if len(addr) > 10 else addr)
        category = vasp.category if vasp else ("target" if is_root else "intermediary")
        risk = vasp.risk_score if vasp else (cluster.risk_score if cluster else 0.50)

        G.add_node(
            addr,
            address=addr,
            label=label,
            cluster_id=cluster.cluster_id if cluster else "unclustered",
            category=category,
            risk_score=risk,
            is_root=is_root,
            is_vasp=vasp.is_vasp if vasp else False,
            inflow_usd=0.0,
            outflow_usd=0.0,
            tx_count=0,
        )

    # Add edges and accumulate node volumes
    for idx, tx in enumerate(transactions):
        G.add_edge(
            tx.from_address,
            tx.to_address,
            key=f"{tx.tx_hash}_{idx}",
            tx_hash=tx.tx_hash,
            amount=tx.amount,
            amount_usd=tx.amount_usd,
            token=tx.token,
            chain=tx.chain,
            timestamp=tx.timestamp.isoformat(),
        )

        if tx.from_address in G.nodes:
            G.nodes[tx.from_address]["outflow_usd"] += tx.amount_usd
            G.nodes[tx.from_address]["tx_count"] += 1
        if tx.to_address in G.nodes:
            G.nodes[tx.to_address]["inflow_usd"] += tx.amount_usd
            G.nodes[tx.to_address]["tx_count"] += 1

    return G, clusters


def export_cytoscape_json(
    G: nx.DiGraph, clusters: dict[str, WalletCluster], root_address: str
) -> dict[str, Any]:
    """
    Serializes NetworkX forensic graph into Cytoscape.js format for frontend graph rendering.
    """
    nodes = []
    edges = []
    total_volume = 0.0
    vasps_found = set()

    for node_id, data in G.nodes(data=True):
        if data.get("is_vasp") and data.get("label"):
            vasps_found.add(data["label"])

        nodes.append({
            "data": {
                "id": str(node_id),
                "label": data.get("label", str(node_id)),
                "cluster_id": data.get("cluster_id", "unclustered"),
                "category": data.get("category", "unknown"),
                "risk_score": round(data.get("risk_score", 0.5), 2),
                "is_root": data.get("is_root", False),
                "is_vasp": data.get("is_vasp", False),
                "inflow_usd": round(data.get("inflow_usd", 0.0), 2),
                "outflow_usd": round(data.get("outflow_usd", 0.0), 2),
                "tx_count": data.get("tx_count", 0),
            }
        })

    for u, v, data in G.edges(data=True):
        vol = data.get("amount_usd", 0.0)
        total_volume += vol
        edges.append({
            "data": {
                "id": f"e_{data.get('tx_hash', f'{u}_{v}')[:16]}_{u[:6]}_{v[:6]}",
                "source": str(u),
                "target": str(v),
                "amount": data.get("amount", 0.0),
                "amount_usd": round(vol, 2),
                "token": data.get("token", "ETH"),
                "chain": data.get("chain", "ethereum"),
                "tx_hash": data.get("tx_hash", ""),
                "timestamp": data.get("timestamp", ""),
            }
        })

    return {
        "elements": {
            "nodes": nodes,
            "edges": edges,
        },
        "summary": {
            "root_address": root_address,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "total_volume_usd": round(total_volume, 2),
            "clusters_count": len(clusters),
            "attributed_vasps": list(vasps_found),
        },
    }


def export_graphml_str(G: nx.DiGraph) -> str:
    """Serializes NetworkX DiGraph to GraphML XML formatted string."""
    import io
    stream = io.BytesIO()
    # Create clean copy with scalar attributes only
    clean_G = nx.DiGraph()
    for n, d in G.nodes(data=True):
        clean_G.add_node(str(n), **{k: str(v) if not isinstance(v, (int, float, bool)) else v for k, v in d.items()})
    for u, v, d in G.edges(data=True):
        clean_G.add_edge(str(u), str(v), **{k: str(val) if not isinstance(val, (int, float, bool)) else val for k, val in d.items()})
    nx.write_graphml(clean_G, stream)
    return stream.getvalue().decode("utf-8")

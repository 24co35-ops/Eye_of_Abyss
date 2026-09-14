"""
Heuristic clustering engine for cryptocurrency forensic analysis.
Implements:
  1. Multi-input Co-spend Heuristic (UTXO clustering)
  2. Change Address Detection Heuristic
  3. Peeling Chain Identification Heuristic
  4. Disjoint Set / Connected-Component Cluster Merging
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Sequence

from services.chaineye.attribution.vasp_registry import get_vasp_attribution
from services.chaineye.graph.explorer import TransactionRecord


@dataclass
class WalletCluster:
    cluster_id: str
    addresses: set[str] = field(default_factory=set)
    entity_tag: str = "Unknown Cluster"
    is_known_vasp: bool = False
    vasp_name: str | None = None
    risk_score: float = 0.50
    total_inflow_usd: float = 0.0
    total_outflow_usd: float = 0.0
    peeling_chain_count: int = 0


class DisjointSet:
    """Standard Union-Find data structure with path compression and union by rank."""

    def __init__(self):
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def find(self, item: str) -> str:
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0
            return item
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item1: str, item2: str):
        root1 = self.find(item1)
        root2 = self.find(item2)
        if root1 != root2:
            if self.rank[root1] < self.rank[root2]:
                self.parent[root1] = root2
            elif self.rank[root1] > self.rank[root2]:
                self.parent[root2] = root1
            else:
                self.parent[root2] = root1
                self.rank[root1] += 1


def apply_cospend_heuristic(transactions: Sequence[TransactionRecord], ds: DisjointSet):
    """
    Co-spend (Multi-input) heuristic:
    All inputs co-spent in a Bitcoin/UTXO transaction belong to the same entity.
    """
    for tx in transactions:
        if tx.co_inputs and len(tx.co_inputs) > 1:
            primary = tx.co_inputs[0]
            for co in tx.co_inputs[1:]:
                ds.union(primary, co)


def detect_peeling_chains(transactions: Sequence[TransactionRecord]) -> list[dict]:
    """
    Peeling chain heuristic:
    Detects patterns where a single source address outputs to 2 destinations:
    - One small payment/service transfer (peeled amount)
    - One large change transfer flowing into the next transaction.
    """
    out_edges = defaultdict(list)
    for tx in transactions:
        out_edges[tx.from_address].append(tx)

    peeling_sequences = []
    for src, tx_list in out_edges.items():
        if len(tx_list) >= 2:
            sorted_tx = sorted(tx_list, key=lambda t: t.amount_usd)
            smaller = sorted_tx[0]
            larger = sorted_tx[-1]
            if smaller.amount_usd < larger.amount_usd and smaller.to_address != larger.to_address:
                peeling_sequences.append({
                    "source": src,
                    "peel_destination": smaller.to_address,
                    "peel_amount_usd": smaller.amount_usd,
                    "change_destination": larger.to_address,
                    "change_amount_usd": larger.amount_usd,
                    "tx_hash": smaller.tx_hash,
                })

    return peeling_sequences


def cluster_wallet_network(
    root_address: str, transactions: Sequence[TransactionRecord]
) -> dict[str, WalletCluster]:
    """
    Executes full heuristic clustering pipeline over transaction history.
    Returns mapping of cluster_id -> WalletCluster.
    """
    ds = DisjointSet()
    ds.find(root_address)

    # 1. Apply multi-input co-spend clustering
    apply_cospend_heuristic(transactions, ds)

    # 2. Detect peeling chains
    peeling_chains = detect_peeling_chains(transactions)
    peeled_sources = {p["source"] for p in peeling_chains}

    # Ensure all transaction addresses exist in disjoint set
    for tx in transactions:
        ds.find(tx.from_address)
        ds.find(tx.to_address)

    # Group addresses by root cluster
    clusters_map: dict[str, set[str]] = defaultdict(set)
    all_addresses = {root_address}
    for tx in transactions:
        all_addresses.add(tx.from_address)
        all_addresses.add(tx.to_address)

    for addr in all_addresses:
        root = ds.find(addr)
        clusters_map[root].add(addr)

    # Calculate volumes and entity attributions per cluster
    inflows: dict[str, float] = defaultdict(float)
    outflows: dict[str, float] = defaultdict(float)

    for tx in transactions:
        outflows[tx.from_address] += tx.amount_usd
        inflows[tx.to_address] += tx.amount_usd

    result: dict[str, WalletCluster] = {}
    for root_id, addrs in clusters_map.items():
        # Check if any address in cluster is a known VASP
        vasp_info = None
        for a in addrs:
            v = get_vasp_attribution(a)
            if v:
                vasp_info = v
                break

        tot_in = sum(inflows[a] for a in addrs)
        tot_out = sum(outflows[a] for a in addrs)
        peel_count = sum(1 for a in addrs if a in peeled_sources)

        if vasp_info:
            entity_tag = vasp_info.name
            risk = vasp_info.risk_score
            is_vasp = vasp_info.is_vasp
            vasp_name = vasp_info.name
        elif peel_count > 0:
            entity_tag = "Peeling Chain Mule Cluster"
            risk = 0.85
            is_vasp = False
            vasp_name = None
        else:
            entity_tag = f"Wallet Cluster ({len(addrs)} addresses)"
            risk = 0.50
            is_vasp = False
            vasp_name = None

        cluster_obj = WalletCluster(
            cluster_id=f"cluster_{root_id[:10]}",
            addresses=addrs,
            entity_tag=entity_tag,
            is_known_vasp=is_vasp,
            vasp_name=vasp_name,
            risk_score=risk,
            total_inflow_usd=round(tot_in, 2),
            total_outflow_usd=round(tot_out, 2),
            peeling_chain_count=peel_count,
        )
        result[cluster_obj.cluster_id] = cluster_obj

    return result

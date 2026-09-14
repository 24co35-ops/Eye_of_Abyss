"""
Neo4j client for the shared criminal actor & cryptocurrency graph.
Stores wallet clusters, transaction flows, and associates them with shared Actor profiles.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional, Sequence

from services.chaineye.graph.clustering import WalletCluster
from services.chaineye.graph.explorer import TransactionRecord

logger = logging.getLogger("chaineye.neo4j")

NEO4J_URI  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "eyeofabyss_dev_2026")


class Neo4jGraphClient:
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASS):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None

    def get_driver(self):
        if self._driver is None:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            except Exception as e:
                logger.warning(f"Could not connect to Neo4j at {self.uri}: {e}")
                self._driver = None
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def sync_trace_graph(
        self,
        root_address: str,
        transactions: Sequence[TransactionRecord],
        clusters: dict[str, WalletCluster],
        actor_id: Optional[str] = None,
    ) -> bool:
        """
        Persists wallet nodes, transaction edges, and clusters into Neo4j graph.
        Optionally attaches wallet nodes to an existing Actor node for cross-module correlation.
        """
        driver = self.get_driver()
        if not driver:
            logger.info("Neo4j driver offline — skipping on-disk graph sync.")
            return False

        try:
            with driver.session() as session:
                # 1. Upsert Wallet nodes
                for cluster in clusters.values():
                    for addr in cluster.addresses:
                        session.run(
                            """
                            MERGE (w:Wallet {address: $address})
                            SET w.cluster_id = $cluster_id,
                                w.entity_tag = $entity_tag,
                                w.risk_score = $risk_score,
                                w.is_vasp = $is_vasp,
                                w.vasp_name = $vasp_name,
                                w.updated_at = datetime()
                            """,
                            address=addr,
                            cluster_id=cluster.cluster_id,
                            entity_tag=cluster.entity_tag,
                            risk_score=cluster.risk_score,
                            is_vasp=cluster.is_known_vasp,
                            vasp_name=cluster.vasp_name or "",
                        )

                # 2. Upsert Transactions & Transfer edges
                for tx in transactions:
                    session.run(
                        """
                        MATCH (src:Wallet {address: $from_addr})
                        MATCH (dst:Wallet {address: $to_addr})
                        MERGE (src)-[r:TRANSFERRED {tx_hash: $tx_hash}]->(dst)
                        SET r.amount_usd = $amount_usd,
                            r.token = $token,
                            r.chain = $chain,
                            r.timestamp = datetime($timestamp)
                        """,
                        from_addr=tx.from_address,
                        to_addr=tx.to_address,
                        tx_hash=tx.tx_hash,
                        amount_usd=tx.amount_usd,
                        token=tx.token,
                        chain=tx.chain,
                        timestamp=tx.timestamp.isoformat(),
                    )

                # 3. Associate with Criminal Actor if linked
                if actor_id:
                    session.run(
                        """
                        MERGE (a:Actor {actor_id: $actor_id})
                        MATCH (w:Wallet {address: $root_addr})
                        MERGE (a)-[:OPERATES_WALLET]->(w)
                        """,
                        actor_id=str(actor_id),
                        root_addr=root_address,
                    )

            return True
        except Exception as e:
            logger.warning(f"Neo4j sync failed: {e}")
            return False

    def query_wallet_subgraph(self, address: str, depth: int = 2) -> dict[str, Any]:
        """Queries 2-hop neighborhood of a wallet address in Neo4j."""
        driver = self.get_driver()
        if not driver:
            return {"nodes": [], "edges": [], "note": "Neo4j offline"}

        try:
            with driver.session() as session:
                result = session.run(
                    """
                    MATCH path = (w:Wallet {address: $address})-[r:TRANSFERRED*1..2]-(other:Wallet)
                    RETURN nodes(path) AS nodes, relationships(path) AS rels
                    LIMIT 100
                    """,
                    address=address,
                )
                nodes_set = {}
                edges_list = []
                for record in result:
                    for n in record["nodes"]:
                        nodes_set[n["address"]] = dict(n)
                    for r in record["rels"]:
                        edges_list.append({
                            "source": r.start_node["address"],
                            "target": r.end_node["address"],
                            "tx_hash": r.get("tx_hash"),
                            "amount_usd": r.get("amount_usd"),
                        })
                return {"nodes": list(nodes_set.values()), "edges": edges_list}
        except Exception as e:
            logger.warning(f"Neo4j query error: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}


# Global default instance
neo4j_client = Neo4jGraphClient()

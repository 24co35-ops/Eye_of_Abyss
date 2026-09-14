"""
Blockchain anchoring stubs — wire Web3 + Pinata when keys are available.
Every function has a clear TODO and matches the flow in design-doc.md §4.
"""

import hashlib
import json
import os
from uuid import UUID


EVIDENCE_REGISTRY_ADDRESS = os.getenv("EVIDENCE_REGISTRY_ADDRESS", "")
POLYGON_RPC_URL           = os.getenv("POLYGON_RPC_URL", "")
PINATA_API_KEY            = os.getenv("PINATA_API_KEY", "")
PINATA_SECRET_KEY         = os.getenv("PINATA_SECRET_KEY", "")


def compute_hash(evidence_dict: dict) -> str:
    """SHA-256 of canonical JSON — deterministic, sort_keys=True."""
    raw = json.dumps(evidence_dict, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


async def pin_to_ipfs(evidence_dict: dict) -> str:
    """
    TODO: POST evidence_dict to Pinata /pinning/pinJSONToIPFS.
    Returns IPFS CID string.
    Requires: PINATA_API_KEY, PINATA_SECRET_KEY
    """
    # ponytail: stub — returns fake CID until Pinata keys are wired
    return "Qm_STUB_CID_" + compute_hash(evidence_dict)[:16]


async def anchor_on_polygon(evidence_hash_hex: str, case_id: str, module_id: str, ipfs_cid: str) -> str:
    """
    TODO: Call EvidenceRegistry.anchor() on Polygon via web3.py.
    Flow from design-doc §4:
      1. Build tx calling contract.functions.anchor(hash, caseId, moduleId, cid)
      2. Sign with PRIVATE_KEY
      3. Send and await receipt
      4. Return tx_hash
    Requires: POLYGON_RPC_URL, PRIVATE_KEY, EVIDENCE_REGISTRY_ADDRESS
    """
    # ponytail: stub — returns fake tx hash until web3 is wired
    return "0xSTUB_TX_" + evidence_hash_hex[:32]

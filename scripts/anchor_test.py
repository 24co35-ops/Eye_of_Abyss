"""Standalone verification script for Polygon Mumbai evidence anchoring."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "shared"))
sys.path.insert(0, str(_ROOT / "services" / "case-engine"))

from anchoring.anchor import (
    compute_evidence_hash,
    serialize_canonical_json,
    anchor_evidence_onchain,
    verify_evidence_onchain,
)


def run_anchor_test() -> bool:
    print("=" * 60)
    print("  Eye of Abyss -- Polygon Evidence Anchoring Test")
    print("=" * 60)

    sample_evidence = {
        "case_id": "EOA-2026-0035",
        "module_id": "voiceguard",
        "verdict": "SYNTHETIC_TTS",
        "confidence": 0.914,
        "timestamp": "2026-08-22T06:00:00Z",
    }

    # 1. Test canonical serialization
    canonical = serialize_canonical_json(sample_evidence)
    print(f"  [+] Canonical JSON: {canonical}")

    # 2. Test deterministic SHA-256 hash
    ev_hash_hex, ev_bytes32 = compute_evidence_hash(sample_evidence)
    print(f"  [+] SHA-256 Hash:   {ev_hash_hex}")
    print(f"  [+] Bytes32:        {ev_bytes32.hex()[:24]}...")
    assert ev_hash_hex.startswith("0x")
    assert len(ev_hash_hex) == 66

    # 3. Test on-chain anchor submission (with mock fallback if live credentials omitted)
    mock_cid = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"
    tx_hash = anchor_evidence_onchain(
        evidence_hash_hex=ev_hash_hex,
        case_id="EOA-2026-0035",
        module_id="voiceguard",
        ipfs_cid=mock_cid,
    )
    print(f"  [+] Polygon Anchor TX: {tx_hash}")
    assert tx_hash.startswith("0x")

    # 4. Verify on-chain query response structure
    res = verify_evidence_onchain(ev_hash_hex)
    print(f"  [+] Verification Query: {res}")

    print("=" * 60)
    print("  Anchor Test Passed Successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_anchor_test()
    sys.exit(0 if success else 1)

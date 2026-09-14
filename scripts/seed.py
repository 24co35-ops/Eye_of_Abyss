"""Seed script with exact sample cases from Eye of Abyss Stitch prompts."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add project root and services to path
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "shared"))
sys.path.insert(0, str(_ROOT / "services" / "case-engine"))

from shared.schemas import Artifact, CaseFile, CrossModuleSignals, EvidenceObject

# ── Owner account seeding ─────────────────────────────────────────────────────
SEED_OWNER_EMAIL    = os.getenv("SEED_OWNER_EMAIL", "owner@eyeofabyss.local")
SEED_OWNER_PASSWORD = os.getenv("SEED_OWNER_PASSWORD", "changeme123")

# Exact cases from Stitch prompts (Prompts 1, 2, 3, 4, 5)
SEED_CASES = [
    {
        "case_id": "00000000-0000-0000-0000-000000000041",
        "case_code": "EOA-2026-0041",
        "complainant_type": "Corporate Fraud (Axis Bank Corporate)",
        "reported_loss": "₹2.4 Cr",
        "modules_assigned": ["voiceguard", "chaineye"],
        "status": "ANCHORED",
        "threat_tier": "T3",
        "created_by": "Insp. R. Mehta",
        "convergence": {
            "timezone_match": 0.92,
            "activity_overlap": 0.88,
            "actor_graph_link": "wallet_1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
            "convergence_confidence": 0.89,
        },
        "anchor_tx_hashes": ["0x3f4ad821a80c9e7821bcfa7812903fead82910ba1234567890abcdef12345678"],
        "evidence": [
            {
                "module_id": "voiceguard",
                "verdict": "Synthetic voice detected (TTS model)",
                "verdict_code": "SYNTHETIC_TTS",
                "confidence": 0.942,
                "confidence_tier": "high",
                "payload": {
                    "synthetic_duration_sec": 62.0,
                    "total_duration_sec": 134.0,
                    "model": "DistilWav2Vec2 + ECAPA-TDNN ensemble",
                    "gan_artifact_detected": True,
                },
                "artifacts": [
                    {"filename": "waveform_analysis.png", "file_type": "image/png", "description": "Audio waveform highlights"},
                    {"filename": "mel_spectrogram.png", "file_type": "image/png", "description": "Mel frequency spectrogram"},
                ],
                "hash_sha256": "4a1c5b8e9f2d3a7c6e1b8a5d3f9c2e7b1a6d8f4e2c9b5a7d1f3e8c2a6b9d4f1e",
                "chain_anchor": "0x3f4ad821a80c9e7821bcfa7812903fead82910ba1234567890abcdef12345678",
                "ipfs_cid": "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco",
            },
            {
                "module_id": "chaineye",
                "verdict": "VASP Attribution: Binance Global; Withdrawal window predicted",
                "verdict_code": "WITHDRAWAL_ALERT",
                "confidence": 0.82,
                "confidence_tier": "high",
                "payload": {
                    "wallet_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
                    "vasp": "Binance Global",
                    "vasp_confidence": 0.82,
                    "predicted_window_start": "2026-09-16T02:00:00Z",
                    "predicted_window_end": "2026-09-16T04:00:00Z",
                    "total_inflow_btc": 4.73,
                    "cluster_size": 12,
                    "mixer_used": True,
                },
                "artifacts": [
                    {"filename": "wallet_cluster_graph.json", "file_type": "application/json", "description": "12-node wallet cluster"},
                    {"filename": "withdrawal_prediction.json", "file_type": "application/json", "description": "T2 dormancy cycle prediction"},
                ],
                "hash_sha256": "8f3e2c9a6b5d1f7e4a8c2b9d6e1f3a5c7b8d4e2a9c1f6b3e8a5d7c2f4b9e1a6d",
                "chain_anchor": "0x7a2bd912ef89c20148ba761042cde90184b291a8e72c89f102ba948192a019be",
                "ipfs_cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
            },
        ],
    },
    {
        "case_id": "00000000-0000-0000-0000-000000000039",
        "case_code": "EOA-2026-0039",
        "complainant_type": "Investment Fraud (Retail Victims Group)",
        "reported_loss": "₹12.5 Lakhs",
        "modules_assigned": ["chaineye"],
        "status": "EVIDENCE_SUBMITTED",
        "threat_tier": "T2",
        "created_by": "Insp. R. Mehta",
        "convergence": None,
        "anchor_tx_hashes": [],
        "evidence": [
            {
                "module_id": "chaineye",
                "verdict": "Arbitrage Scam Pool Traced to FixedFloat",
                "verdict_code": "VASP_ATTRIBUTED",
                "confidence": 0.79,
                "confidence_tier": "medium",
                "payload": {"wallet": "0x4c9edd5852cd905f086c759e8383e09bff1e68b3", "vasp": "FixedFloat"},
                "artifacts": [{"filename": "flow.json", "file_type": "application/json", "description": "Fund flow trace"}],
                "hash_sha256": "3c9a1f6e2b8d5a7c4f1e8b2d9a6c3e7f1b5d8a2c4e9f7b1a6d3c8e5f2b9a7d1c",
                "chain_anchor": None,
                "ipfs_cid": None,
            }
        ],
    },
    {
        "case_id": "00000000-0000-0000-0000-000000000037",
        "case_code": "EOA-2026-0037",
        "complainant_type": "Voice Vishing (Senior Citizen Impersonation)",
        "reported_loss": "₹5.8 Lakhs",
        "modules_assigned": ["voiceguard"],
        "status": "ACTIVE",
        "threat_tier": "T1",
        "created_by": "Insp. R. Mehta",
        "convergence": None,
        "anchor_tx_hashes": [],
        "evidence": [
            {
                "module_id": "voiceguard",
                "verdict": "Synthetic voice detected — Vishing Call Recording",
                "verdict_code": "SYNTHETIC_VOICE_CONVERSION",
                "confidence": 0.914,
                "confidence_tier": "high",
                "payload": {"verdict": "SYNTHETIC", "tts_segments": 2, "vc_segments": 1},
                "artifacts": [{"filename": "audio_analysis.json", "file_type": "application/json", "description": "Segment breakdown"}],
                "hash_sha256": "1f8e2c4a9b6d3a7e5f1c8b2d4a9c6e3f7b5d1a8c2e4f9b7a3d6c8e1f5b2a9d7c",
                "chain_anchor": None,
                "ipfs_cid": None,
            }
        ],
    },
    {
        "case_id": "00000000-0000-0000-0000-000000000035",
        "case_code": "EOA-2026-0035",
        "complainant_type": "Dark Web Vendor (Redacted Corporate Entity)",
        "reported_loss": "₹47.3 Lakhs",
        "modules_assigned": ["voiceguard", "shadowtrace", "chaineye"],
        "status": "CONVERGENCE_COMPUTED",
        "threat_tier": "T2",
        "created_by": "Insp. R. Mehta",
        "convergence": {
            "timezone_match": 0.79,
            "activity_overlap": 1.0,
            "actor_graph_link": "d4rk_exch4nger -> 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
            "convergence_confidence": 0.81,
        },
        "anchor_tx_hashes": [],
        "evidence": [
            {
                "module_id": "voiceguard",
                "verdict": "AI-generated voice (TTS) confirmed in 3 call segments",
                "verdict_code": "SYNTHETIC_TTS",
                "confidence": 0.914,
                "confidence_tier": "high",
                "payload": {"evidence_id": "EV-VG-2026-0891"},
                "artifacts": [
                    {"filename": "waveform.png", "file_type": "image/png", "description": "Waveform"},
                    {"filename": "spectrogram.png", "file_type": "image/png", "description": "Mel Spectrogram"},
                ],
                "hash_sha256": "6b2e1f4a9c8d3a7e5f1b8a2d4c9e6f3a7b5d1c8e2f4a9b7d3c6e8f1a5b2d9c7e",
                "chain_anchor": None,
                "ipfs_cid": None,
            },
            {
                "module_id": "shadowtrace",
                "verdict": "d4rk_exch4nger (AlphaBay <-> Telegram confirmed)",
                "verdict_code": "ACTOR_ATTRIBUTED",
                "confidence": 0.87,
                "confidence_tier": "high",
                "payload": {"evidence_id": "EV-ST-2026-0445", "actor_handle": "d4rk_exch4nger"},
                "artifacts": [
                    {"filename": "fingerprint.json", "file_type": "application/json", "description": "Radar fingerprint"},
                    {"filename": "actor_graph.graphml", "file_type": "application/xml", "description": "Force-directed graph"},
                    {"filename": "attribution_report.pdf", "file_type": "application/pdf", "description": "Stylometry report"},
                ],
                "hash_sha256": "9a1c8f3e2b5d7a4c6e1f8b2d9a6c3e7f1b5d8a2c4e9f7b1a6d3c8e5f2b9a7d1e",
                "chain_anchor": None,
                "ipfs_cid": None,
            },
            {
                "module_id": "chaineye",
                "verdict": "Binance Global — 4.73 BTC traced across 12 wallets. Withdrawal window: Sep 16",
                "verdict_code": "WITHDRAWAL_WINDOW_COMPUTED",
                "confidence": 0.82,
                "confidence_tier": "high",
                "payload": {"evidence_id": "EV-CE-2026-0312", "vasp": "Binance Global", "amount_btc": 4.73},
                "artifacts": [
                    {"filename": "wallet_graph.json", "file_type": "application/json", "description": "Cluster graph"},
                    {"filename": "transaction_log.csv", "file_type": "text/csv", "description": "Transaction history"},
                ],
                "hash_sha256": "2d9a6c3e7f1b5d8a2c4e9f7b1a6d3c8e5f2b9a7d1e9a1c8f3e2b5d7a4c6e1f8b",
                "chain_anchor": None,
                "ipfs_cid": None,
            },
        ],
    },
    {
        "case_id": "00000000-0000-0000-0000-000000000031",
        "case_code": "EOA-2026-0031",
        "complainant_type": "Corporate Ransomware (Critical Infrastructure)",
        "reported_loss": "₹1.2 Cr",
        "modules_assigned": ["voiceguard", "shadowtrace", "chaineye"],
        "status": "FILED",
        "threat_tier": "T3",
        "created_by": "Insp. R. Mehta",
        "convergence": {
            "timezone_match": 0.88,
            "activity_overlap": 0.94,
            "actor_graph_link": "lock_cipher_88",
            "convergence_confidence": 0.91,
        },
        "anchor_tx_hashes": ["0x9812ba9c8e712345091823abce128790184b291a8e72c89f102ba948192a019b"],
        "evidence": [],
    },
]


async def seed_database():
    """Seeds cases and evidence into PostgreSQL or local JSON cache."""
    print("=" * 60)
    print("  Eye of Abyss -- Database & Fixture Seeding")
    print("=" * 60)

    # 1. Write static fixtures JSON for frontend / offline dev
    fixtures_dir = _ROOT / "frontend" / "public" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    cases_fixture_path = fixtures_dir / "cases.json"
    with open(cases_fixture_path, "w", encoding="utf-8") as f:
        json.dump(SEED_CASES, f, indent=2)
    print(f"  [+] Static fixtures written to {cases_fixture_path}")

    # 2. Try DB seeding if PostgreSQL is available
    try:
        from db import Case, Evidence, SessionLocal, User, create_tables
        from sqlalchemy import select
        from passlib.context import CryptContext

        _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

        await create_tables()
        async with SessionLocal() as db:
            # Seed OWNER account (idempotent)
            existing_owner = await db.scalar(select(User).where(User.email == SEED_OWNER_EMAIL))
            if not existing_owner:
                owner = User(
                    email=SEED_OWNER_EMAIL,
                    hashed_password=_pwd.hash(SEED_OWNER_PASSWORD),
                    role="OWNER",
                    is_active=True,
                )
                db.add(owner)
                await db.commit()
                print(f"  [+] OWNER account seeded: {SEED_OWNER_EMAIL}")
            else:
                print(f"  [=] OWNER account already exists: {SEED_OWNER_EMAIL}")

            for item in SEED_CASES:
                uid = uuid.UUID(item["case_id"])
                existing = (await db.execute(select(Case).where(Case.case_id == uid))).scalar_one_or_none()
                if not existing:
                    c = Case(
                        case_id=uid,
                        status=item["status"],
                        created_by=item["created_by"],
                        complainant_type=item["complainant_type"],
                        reported_loss=item["reported_loss"],
                        modules_assigned=item["modules_assigned"],
                        convergence=item["convergence"],
                        anchor_tx_hashes=item["anchor_tx_hashes"],
                    )
                    db.add(c)
                    await db.flush()

                    for ev in item.get("evidence", []):
                        e = Evidence(
                            evidence_id=uuid.uuid4(),
                            case_id=uid,
                            module_id=ev["module_id"],
                            submitted_by=item["created_by"],
                            created_by=item["created_by"],
                            verdict=ev["verdict"],
                            verdict_code=ev["verdict_code"],
                            confidence=ev["confidence"],
                            confidence_tier=ev["confidence_tier"],
                            payload=ev.get("payload", {}),
                            artifacts=ev.get("artifacts", []),
                            hash_sha256=ev["hash_sha256"],
                            chain_anchor=ev.get("chain_anchor"),
                            ipfs_cid=ev.get("ipfs_cid"),
                        )
                        db.add(e)
            await db.commit()
        print("  [+] PostgreSQL database seeded with active demo cases.")
    except Exception as exc:
        print(f"  [-] Database direct connection skipped ({exc}). Static cache ready.")

    print("=" * 60)
    print("  Seed Complete -- 5 Canonical Cases + OWNER account ready")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())

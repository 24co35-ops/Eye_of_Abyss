"""Generates synthetic NCRP (National Cyber Crime Reporting Portal) complaints correlated with actor profiles."""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from shared.schemas import CriminalActorProfile

COMPLAINANT_CATEGORIES = {
    "investment_fraudster": ["Corporate Fraud", "High-Yield Investment Scam", "Cryptocurrency Arbitrage Fraud", "Ponzi Scheme"],
    "darknet_vendor": ["Dark Web Contraband", "Illicit Marketplace Vendor", "Escrow Extortion"],
    "ransomware_operator": ["Corporate Ransomware Attack", "Data Exfiltration Extortion", "Critical Infrastructure Ransom"],
    "romance_scammer": ["Matrimonial / Romance Scam", "Customs Clearance Impersonation", "Overseas Wire Fraud"],
    "mule_recruiter": ["Illegal Mule Account Recruitment", "Unauthorized OTC Settlement", "Money Mule Ring"],
}

USD_TO_INR = 83.5


def generate_complaints(
    actors: List[CriminalActorProfile],
    transactions: Optional[List[Dict[str, any]]] = None,
    start_date: Optional[datetime] = None,
) -> List[Dict[str, any]]:
    """
    Generates synthetic NCRP complaints linked to actors, cases, and victim losses.
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=21)

    complaints: List[Dict[str, any]] = []

    # Map actor_id to their first transaction if available
    tx_by_actor: Dict[str, str] = {}
    if transactions:
        for tx in transactions:
            aid = tx.get("actor_id")
            if aid and aid not in tx_by_actor:
                tx_by_actor[aid] = tx.get("tx_hash", "")

    for i, actor in enumerate(actors):
        archetype = actor.archetype
        categories = COMPLAINANT_CATEGORIES.get(archetype, ["Cyber Financial Fraud"])
        category = random.choice(categories)

        base_vol_usd = actor.transaction_features.get("base_volume_usd", 25000.0)
        # Victim loss is a realistic fraction or total of the base volume
        loss_usd = round(base_vol_usd * random.uniform(0.3, 1.0), 2)
        loss_inr = round(loss_usd * USD_TO_INR, 2)

        suspect_wallet = actor.wallet_addresses[0] if actor.wallet_addresses else f"0x{hashlib.sha256(str(actor.actor_id).encode()).hexdigest()[:40]}"
        tx_hash = tx_by_actor.get(str(actor.actor_id), f"0x{hashlib.sha256(f'complaint_tx_{actor.actor_id}'.encode()).hexdigest()}")

        # Case ID formatted as EOA-2026-XXXX
        case_seq = 1000 + (i % 9000)
        case_id = f"EOA-2026-{case_seq:04d}"
        complaint_id = f"NCRP-2026-{random.randint(100000, 999999)}"

        complaint_time = start_date + timedelta(days=random.randint(1, 14), hours=random.randint(8, 20), minutes=random.randint(0, 59))

        complaints.append({
            "complaint_id": complaint_id,
            "case_id": case_id,
            "actor_id": str(actor.actor_id),
            "complainant_category": category,
            "reported_loss_inr": loss_inr,
            "reported_loss_usd": loss_usd,
            "suspect_wallet": suspect_wallet,
            "tx_hash": tx_hash,
            "timestamp": complaint_time.isoformat(),
            "data_source": "synthetic",
        })

    return complaints

"""
Synthetic transaction graph generator for ChainEye.
Generates realistic multi-hop criminal flows matching CriminalActorProfile archetypes
(e.g. investment_fraudster, darknet_vendor, ransomware_operator).
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from shared.schemas import CriminalActorProfile
from services.chaineye.graph.explorer import TransactionRecord


def generate_synthetic_actor_flow(
    actor_profile: Optional[CriminalActorProfile] = None,
    chain: str = "ethereum",
    base_volume_usd: float = 75000.0,
) -> tuple[CriminalActorProfile, list[TransactionRecord]]:
    """
    Generates synthetic on-chain transaction trail for a criminal actor profile.
    Correlates active hours, timezone, and cashout patterns.
    """
    if actor_profile is None:
        actor_id = uuid4()
        archetype = random.choice(["investment_fraudster", "darknet_vendor", "ransomware_operator"])
        root_addr = f"0x{hashlib.sha256(str(actor_id).encode()).hexdigest()[:40]}"
        active_hours = [20, 21, 22, 23, 0, 1] if archetype == "investment_fraudster" else [2, 3, 4, 5]
        
        actor_profile = CriminalActorProfile(
            actor_id=actor_id,
            archetype=archetype,
            handles=[f"shadow_{archetype[:4]}_{random.randint(100, 999)}"],
            platforms=["Telegram", "BreachForums", "Dread"],
            timezone="UTC" if 0 in active_hours else "UTC+5:30",
            active_hours=active_hours,
            wallet_addresses=[root_addr],
            transaction_features={
                "base_volume_usd": base_volume_usd,
                "preferred_vasp": "Binance" if archetype == "investment_fraudster" else "FixedFloat",
                "uses_mixer": archetype in ("darknet_vendor", "ransomware_operator"),
            },
            data_source="synthetic",
        )

    root_addr = actor_profile.wallet_addresses[0] if actor_profile.wallet_addresses else f"0x{hashlib.sha256(str(actor_profile.actor_id).encode()).hexdigest()[:40]}"
    
    # Generate on-chain transactions aligned with active hours
    records: list[TransactionRecord] = []
    base_time = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Target destinations
    destinations = [
        ("0x71c83638379185a61142b19127765f14f0d6498b", "Binance Hot Wallet 6"),
        ("0x4c9edd5852cd905f086c759e8383e09bff1e68b3", "FixedFloat Hot Wallet"),
        ("0xd90e2f925da726b50c4ed8d0fb90ad053324f31b", "Tornado.Cash Pool"),
    ]

    current_src = root_addr
    remaining_vol = base_volume_usd
    eth_price = 3500.0

    for hop in range(1, 4):
        # Pick hour from actor's active hours
        peak_hour = actor_profile.active_hours[0] if actor_profile.active_hours else 21
        tx_time = base_time + timedelta(days=hop, hours=peak_hour)
        
        peel_usd = remaining_vol * 0.60
        change_usd = remaining_vol * 0.40
        
        peel_dest, _ = destinations[(hop - 1) % len(destinations)]
        change_dest = f"0x{hashlib.sha256(f'{current_src}_mule_{hop}'.encode()).hexdigest()[:40]}"
        
        # Peeling transfer
        records.append(
            TransactionRecord(
                tx_hash=f"0x{hashlib.sha256(f'synth_{current_src}_{peel_dest}_{hop}'.encode()).hexdigest()}",
                from_address=current_src,
                to_address=peel_dest,
                amount=round(peel_usd / eth_price, 4),
                amount_usd=round(peel_usd, 2),
                token="ETH",
                timestamp=tx_time,
                chain=chain,
                block_number=19500000 + hop * 50,
            )
        )

        # Change transfer
        records.append(
            TransactionRecord(
                tx_hash=f"0x{hashlib.sha256(f'synth_{current_src}_{change_dest}_{hop}'.encode()).hexdigest()}",
                from_address=current_src,
                to_address=change_dest,
                amount=round(change_usd / eth_price, 4),
                amount_usd=round(change_usd, 2),
                token="ETH",
                timestamp=tx_time + timedelta(minutes=15),
                chain=chain,
                block_number=19500000 + hop * 50 + 1,
            )
        )

        current_src = change_dest
        remaining_vol = change_usd

    return actor_profile, records

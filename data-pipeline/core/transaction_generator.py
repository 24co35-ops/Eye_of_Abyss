"""Generates synthetic on-chain transaction records correlated with CriminalActorProfile."""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

from shared.schemas import CriminalActorProfile

KNOWN_VASPS = [
    ("0x71c83638379185a61142b19127765f14f0d6498b", "Binance Global Hot Wallet 6"),
    ("0x4c9edd5852cd905f086c759e8383e09bff1e68b3", "FixedFloat Hot Wallet"),
    ("0x2910543af39aba0cd09dbb2d50200b3e800a63d2", "Kraken Depository 2"),
    ("0x503828976d22510aad0201ac7ec88293211d23da", "Coinbase Prime Custody"),
]

MIXER_POOLS = [
    ("0xd90e2f925da726b50c4ed8d0fb90ad053324f31b", "Tornado.Cash 100 ETH Pool"),
    ("0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc", "Tornado.Cash 10 ETH Pool"),
    ("bc1qwasabimixerpool99x90k213jfa98231kjdf98", "Wasabi CoinJoin Coordinator"),
]


def generate_transactions(
    actors: List[CriminalActorProfile],
    start_date: Optional[datetime] = None,
) -> List[Dict[str, any]]:
    """
    Generates a list of on-chain transaction records for a collection of CriminalActorProfiles.
    All records adhere to the actor's active hours, volume, and mixer usage.
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=28)

    transactions: List[Dict[str, any]] = []

    for actor in actors:
        tx_features = actor.transaction_features or {}
        base_volume = tx_features.get("base_volume_usd", 50000.0)
        uses_mixer = tx_features.get("uses_mixer", False)
        preferred_vasp_name = tx_features.get("preferred_vasp", "Binance Global")

        root_wallet = actor.wallet_addresses[0] if actor.wallet_addresses else f"0x{hashlib.sha256(str(actor.actor_id).encode()).hexdigest()[:40]}"
        chain = "ethereum" if root_wallet.startswith("0x") else ("bitcoin" if root_wallet.startswith("bc1") or root_wallet.startswith("1") else "tron")
        token = "ETH" if chain == "ethereum" else ("BTC" if chain == "bitcoin" else "USDT")
        token_price = 3500.0 if token == "ETH" else (65000.0 if token == "BTC" else 1.0)

        current_src = root_wallet
        remaining_vol = base_volume
        hops = random.randint(2, 5)

        for hop in range(1, hops + 1):
            # Select transaction hour from actor's active hours
            hour = random.choice(actor.active_hours) if actor.active_hours else random.randint(0, 23)
            tx_time = start_date + timedelta(days=hop * 3 + random.randint(0, 2), hours=hour, minutes=random.randint(0, 59))

            # Determine destination (Mixer, VASP, or Mule wallet)
            is_final_hop = (hop == hops)
            is_mixer_tx = False
            vasp_label = ""

            if uses_mixer and hop == 2:
                # Route through mixer pool
                dest_addr, dest_name = random.choice(MIXER_POOLS)
                is_mixer_tx = True
                vasp_label = dest_name
                split_ratio = 0.85
            elif is_final_hop:
                # Final cashout to VASP
                vasp_addr, vasp_name = random.choice(KNOWN_VASPS)
                dest_addr = vasp_addr
                vasp_label = preferred_vasp_name or vasp_name
                split_ratio = 1.0
            else:
                # Peeling hop to intermediate mule
                dest_addr = f"0x{hashlib.sha256(f'{current_src}_mule_{hop}'.encode()).hexdigest()[:40]}" if chain == "ethereum" else f"bc1q{hashlib.sha256(f'{current_src}_mule_{hop}'.encode()).hexdigest()[:38]}"
                split_ratio = 0.60

            tx_vol_usd = round(remaining_vol * split_ratio, 2)
            amount_token = round(tx_vol_usd / token_price, 4)

            tx_hash = f"0x{hashlib.sha256(f'synth_tx_{actor.actor_id}_{hop}_{current_src}_{dest_addr}'.encode()).hexdigest()}"

            transactions.append({
                "tx_hash": tx_hash,
                "from_address": current_src,
                "to_address": dest_addr,
                "amount": amount_token,
                "amount_usd": tx_vol_usd,
                "token": token,
                "timestamp": tx_time.isoformat(),
                "chain": chain,
                "actor_id": str(actor.actor_id),
                "vasp_attribution": vasp_label,
                "is_mixer": is_mixer_tx,
                "data_source": "synthetic",
            })

            # Create change output if peeling
            if split_ratio < 1.0:
                change_vol = round(remaining_vol * (1.0 - split_ratio), 2)
                change_addr = f"0x{hashlib.sha256(f'{current_src}_change_{hop}'.encode()).hexdigest()[:40]}" if chain == "ethereum" else f"bc1q{hashlib.sha256(f'{current_src}_change_{hop}'.encode()).hexdigest()[:38]}"
                change_tx_hash = f"0x{hashlib.sha256(f'synth_change_{actor.actor_id}_{hop}_{change_addr}'.encode()).hexdigest()}"

                transactions.append({
                    "tx_hash": change_tx_hash,
                    "from_address": current_src,
                    "to_address": change_addr,
                    "amount": round(change_vol / token_price, 4),
                    "amount_usd": change_vol,
                    "token": token,
                    "timestamp": (tx_time + timedelta(minutes=random.randint(5, 45))).isoformat(),
                    "chain": chain,
                    "actor_id": str(actor.actor_id),
                    "vasp_attribution": "",
                    "is_mixer": False,
                    "data_source": "synthetic",
                })

                current_src = change_addr
                remaining_vol = change_vol
            else:
                break

    return transactions

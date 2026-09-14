"""Generates synthetic CriminalActorProfile objects with cross-domain correlations."""

from __future__ import annotations

import hashlib
import random
from typing import List, Optional
from uuid import UUID, uuid4

from faker import Faker

try:
    from shared.schemas import CriminalActorProfile
except ImportError:
    # Fallback if shared is not installed in PYTHONPATH
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.schemas import CriminalActorProfile

fake = Faker()

ARCHETYPE_CONFIGS = {
    "investment_fraudster": {
        "platforms": ["Telegram", "WhatsApp", "Instagram", "Dread"],
        "timezones": ["UTC+5:30", "UTC+3", "UTC+4", "UTC+8"],
        "active_hour_blocks": [[10, 11, 12, 14, 15, 16, 17, 18, 19, 20], [18, 19, 20, 21, 22, 23, 0, 1]],
        "handle_prefixes": ["vip_crypto", "trade_master", "yield_king", "alpha_arbitrage", "apex_signals", "phantom_payout"],
        "wallet_chains": ["ethereum", "tron", "bitcoin"],
        "preferred_vasp": ["Binance Global", "Bybit", "WazirX", "CoinDCX"],
        "uses_mixer_prob": 0.25,
        "volume_range_usd": (15000.0, 350000.0),
        "dormancy_days_range": (3, 14),
    },
    "darknet_vendor": {
        "platforms": ["Dread", "AlphaBay", "Empire Market", "Telegram", "Exploit.in"],
        "timezones": ["UTC+1", "UTC+2", "UTC+0", "UTC-5"],
        "active_hour_blocks": [[16, 17, 18, 19, 20, 21, 22, 23, 0, 1], [0, 1, 2, 3, 4, 5]],
        "handle_prefixes": ["stealth_drop", "vendorX", "d4rk_exch4nger", "shadow_pack", "chem_wholesale", "nexus_escrow"],
        "wallet_chains": ["bitcoin", "ethereum"],
        "preferred_vasp": ["FixedFloat", "Kraken", "Huobi", "OKX"],
        "uses_mixer_prob": 0.85,
        "volume_range_usd": (25000.0, 600000.0),
        "dormancy_days_range": (7, 21),
    },
    "ransomware_operator": {
        "platforms": ["Tox", "RansomLeak", "Exploit.in", "XSS.is", "Telegram"],
        "timezones": ["UTC+3", "UTC+4", "UTC+0"],
        "active_hour_blocks": [[1, 2, 3, 4, 5, 6], [20, 21, 22, 23, 0, 1]],
        "handle_prefixes": ["lock_cipher", "abyss_payload", "vault_breaker", "decrypt_support", "zero_leak"],
        "wallet_chains": ["bitcoin", "ethereum"],
        "preferred_vasp": ["FixedFloat", "Bitzlato", "Garantex"],
        "uses_mixer_prob": 0.95,
        "volume_range_usd": (100000.0, 2500000.0),
        "dormancy_days_range": (14, 45),
    },
    "romance_scammer": {
        "platforms": ["Tinder", "WhatsApp", "Telegram", "Facebook"],
        "timezones": ["UTC+1", "UTC+5:30", "UTC-4"],
        "active_hour_blocks": [[8, 9, 12, 13, 19, 20, 21, 22]],
        "handle_prefixes": ["david_consulting", "capt_mark", "dr_alex_offshore", "michael_engineer"],
        "wallet_chains": ["ethereum", "tron", "bitcoin"],
        "preferred_vasp": ["Binance Global", "Paxful", "Remitano"],
        "uses_mixer_prob": 0.15,
        "volume_range_usd": (5000.0, 85000.0),
        "dormancy_days_range": (2, 7),
    },
    "mule_recruiter": {
        "platforms": ["Telegram", "WhatsApp", "Quickr", "LinkedIn"],
        "timezones": ["UTC+5:30", "UTC+3", "UTC+8"],
        "active_hour_blocks": [[9, 10, 11, 12, 14, 15, 16, 17, 18]],
        "handle_prefixes": ["cash_swift", "fast_jobs_daily", "remit_coordinator", "peer_settle_hub"],
        "wallet_chains": ["tron", "ethereum"],
        "preferred_vasp": ["Binance Global", "WazirX", "CoinSwitch"],
        "uses_mixer_prob": 0.30,
        "volume_range_usd": (8000.0, 120000.0),
        "dormancy_days_range": (1, 5),
    },
}


def _generate_wallet_address(chain: str, seed: str) -> str:
    """Generates realistic synthetic wallet addresses for given chain."""
    h = hashlib.sha256(seed.encode()).hexdigest()
    if chain == "bitcoin":
        # Native SegWit or legacy
        return f"bc1q{h[:38]}" if random.random() > 0.4 else f"1{h[:33]}"
    elif chain == "tron":
        return f"T{h[:33]}"
    else:  # ethereum / polygon
        return f"0x{h[:40]}"


def generate_actor_profile(
    archetype: Optional[str] = None,
    actor_id: Optional[UUID] = None,
    seed: Optional[int] = None,
) -> CriminalActorProfile:
    """Generate a single CriminalActorProfile with cross-domain signals."""
    if seed is not None:
        random.seed(seed)

    uid = actor_id or uuid4()
    if not archetype or archetype not in ARCHETYPE_CONFIGS:
        archetype = random.choice(list(ARCHETYPE_CONFIGS.keys()))

    cfg = ARCHETYPE_CONFIGS[archetype]

    # Correlated platforms and handles
    num_platforms = random.randint(2, min(4, len(cfg["platforms"])))
    platforms = random.sample(cfg["platforms"], num_platforms)

    prefix = random.choice(cfg["handle_prefixes"])
    suffix = random.randint(10, 999)
    primary_handle = f"{prefix}_{suffix}"
    handles = [primary_handle]
    if random.random() > 0.3:
        handles.append(f"{prefix}_backup")

    timezone = random.choice(cfg["timezones"])
    active_hours = random.choice(cfg["active_hour_blocks"])

    # Wallet generation
    wallets = []
    for i in range(random.randint(1, 3)):
        chain = random.choice(cfg["wallet_chains"])
        w_addr = _generate_wallet_address(chain, f"{uid}_{i}_{archetype}")
        wallets.append(w_addr)

    vol_min, vol_max = cfg["volume_range_usd"]
    vol_usd = round(random.uniform(vol_min, vol_max), 2)
    dorm_min, dorm_max = cfg["dormancy_days_range"]
    dorm_days = random.randint(dorm_min, dorm_max)
    uses_mixer = random.random() < cfg["uses_mixer_prob"]
    vasp = random.choice(cfg["preferred_vasp"])

    # Stylometric linguistic profile
    linguistic_features = {
        "ttr": round(random.uniform(0.45, 0.78), 3),
        "avg_sentence_len": round(random.uniform(6.5, 18.2), 1),
        "punctuation_rate": round(random.uniform(0.02, 0.12), 3),
        "typo_rate": round(random.uniform(0.01, 0.09), 3),
        "yules_k": round(random.uniform(85.0, 190.0), 1),
    }

    transaction_features = {
        "base_volume_usd": vol_usd,
        "preferred_vasp": vasp,
        "uses_mixer": uses_mixer,
        "dormancy_cycle_days": dorm_days,
        "cluster_wallet_count": random.randint(3, 16),
        "chains": list(set(cfg["wallet_chains"])),
    }

    return CriminalActorProfile(
        actor_id=uid,
        archetype=archetype,
        handles=handles,
        platforms=platforms,
        timezone=timezone,
        active_hours=active_hours,
        wallet_addresses=wallets,
        linguistic_features=linguistic_features,
        transaction_features=transaction_features,
        data_source="synthetic",
    )


def generate_actor_profiles(
    count: int = 100,
    archetypes: Optional[List[str]] = None,
) -> List[CriminalActorProfile]:
    """Generate count CriminalActorProfile instances across selected archetypes."""
    valid_archetypes = list(ARCHETYPE_CONFIGS.keys())
    if archetypes:
        chosen = [a for a in archetypes if a in ARCHETYPE_CONFIGS]
        if not chosen:
            chosen = valid_archetypes
    else:
        chosen = valid_archetypes

    profiles: List[CriminalActorProfile] = []
    for i in range(count):
        arch = chosen[i % len(chosen)]
        profiles.append(generate_actor_profile(archetype=arch))

    return profiles

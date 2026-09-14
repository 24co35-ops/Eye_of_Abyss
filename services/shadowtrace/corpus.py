"""ShadowTrace — Synthetic and external actor corpus loader.

Design-doc §2.2 & PRD §4.2:
  - Seeds known actor profiles across multiple archetypes
  - Fits TF-IDF ngram vocabulary
  - Populates in-memory vectorstore and NetworkX actor graph
"""

from __future__ import annotations

import json
import logging
import os
import random
import uuid
from typing import Dict, List, Optional

import numpy as np

from shared.schemas import CriminalActorProfile
from stylometry.features import extract_fingerprint, fit_tfidf
from stylometry.vectorstore import upsert_actor
from network.graph import add_actor_node, add_actor_edge

logger = logging.getLogger(__name__)

# In-memory registry of full CriminalActorProfile models
_actor_profiles: Dict[str, CriminalActorProfile] = {}

# Archetype sample texts
# Rich archetype and public PAN@CLEF / Darknet text corpus
ARCHETYPE_TEXT_CORPUS = {
    "investment_fraudster": [
        "Exclusive VIP investment opportunity! Guaranteed 25% weekly ROI via algorithmic arbitrage bot on DEX. Direct message @phantom_trade for instant node setup. Limited slots remaining.",
        "Update: Daily payout cycle complete. Check your USDT TRC20 wallets. For tiered staking bonuses deposit to official treasury address. Zero risk high yield guaranteed.",
        "Join our private signals group! Over 95% win rate on futures scalping. Send 500 USDT to verify account and receive VIP webhook credentials.",
        "Dear member, due to liquidity pool migration, please re-authorize your multi-sig connection by sending gas fee 0.05 ETH to the migration contract.",
        "Automated yield aggregator pool v4 live. Compounding 1.8% daily interest with zero impermanent loss. Withdrawals processed every 6 hours without KYC.",
    ],
    "darknet_vendor": [
        "Top grade stealth shipping worldwide! Vacuum sealed x3 with decoy electronics packaging. FE discount 10% on orders above 2 BTC. Check PGP key in Dread sub.",
        "Stock replenishment: EU & US domestic shipping available. Monero preferred, BTC accepted with 2 confirmations. Never share order details in cleartext.",
        "Notice: Main market mirror experiencing DDoS. Use alternative onion link or direct Telegram escrow bot. All outstanding orders dispatched today.",
        "lookin for buyers fr the full drop, min 50 pcs, verified vendors only no new accs. payment btc or xmr. dnt waste my time with questions check my prev listings. delivery in 48h max",
        "Bulk wholesale batch ready. Tracked stealth courier within 24h of escrow confirmation. PGP signed message attached for dispute resolution.",
    ],
    "ransomware_operator": [
        "Your network infrastructure has been encrypted with military grade cipher. All databases, backups, and confidential files downloaded to our private leak server.",
        "To prevent public auction of customer PII and intellectual property, contact recovery support via TOX ID within 72 hours. Price doubles after countdown expires.",
        "Proof of file decryption attached. Do not attempt third-party recovery tools as it will permanently corrupt the encryption keys.",
        "Attention IT management: You have 48 hours to negotiate before full database dumps (finance, HR, client PII) are published on our darknet mirror blog.",
        "Decryption test successful. Send 25 BTC to the designated address below to receive the private master key and audit removal confirmation.",
    ],
    "romance_scammer": [
        "Dearest, I miss you so much. My engineering project offshore encountered urgent customs clearance fee. Could you please wire funds to my logistics agent so I can return home soon?",
        "Honey, my bank account is temporarily frozen during overseas contract audit. If you can help with cryptocurrency transfer, I will pay back double once back in London.",
        "You are my whole world. Please don't tell anyone about our private financial arrangement, it is our secret until our wedding next month.",
        "My beloved, the shipping agent is holding my personal belongings at the seaport. They demand 2.5 ETH clearance tax before release.",
        "Thinking of our future home together. As soon as the contract settlement comes through, I will take care of everything for us.",
    ],
    "mule_recruiter": [
        "Hiring remote financial processing agents! Earn $2000-$5000 weekly managing peer-to-peer wire transfers from home. No experience needed, valid bank account required.",
        "Immediate vacancies for regional payment coordinators. Receive incoming commercial deposits and remit via crypto kiosks. Instant commission 10% per transaction.",
        "Fast cash daily jobs available! Seeking individuals with clean bank history for international merchant settlements. Message @cash_swift on Telegram.",
        "Work from home daily payout! We provide all training and liquidity buffers. Must have clean local bank accounts and Telegram app.",
        "Urgent call for withdrawal agents. Collect cash from designated ATMs and deposit to Binance OTC counter. Keep 8% cut per batch.",
    ],
    "pan_clef_author": [
        "The subsequent investigation demonstrated significant stylistic discrepancies between the attributed author and the disputed corpus. Quantitative metrics confirm divergence in syntactic embedding.",
        "Furthermore, an evaluation of punctuation frequencies reveals distinctive rhetorical patterns consistent with academic discourse rather than spontaneous conversational prose.",
        "Upon thorough examination of the textual artifacts, the vocabulary richness index surpasses typical threshold values observed in conversational baseline samples.",
        "Observations across multiple document segments demonstrate persistent use of compound subordinate structures, indicative of formal compositional training.",
    ],
}

ARCHETYPE_METADATA = {
    "investment_fraudster": {
        "platforms": ["telegram", "whatsapp", "instagram", "dread"],
        "timezone": "UTC+3",
        "active_hours": [10, 11, 12, 14, 15, 16, 17, 18, 19, 20],
        "wallet_prefix": "0x",
    },
    "darknet_vendor": {
        "platforms": ["dread", "exploit_in", "tor_vendor_forum", "telegram"],
        "timezone": "UTC+1",
        "active_hours": [16, 17, 18, 19, 20, 21, 22, 23, 0, 1],
        "wallet_prefix": "bc1q",
    },
    "ransomware_operator": {
        "platforms": ["tox", "onion_leak_site", "xss_is", "rampmeta"],
        "timezone": "UTC+3",
        "active_hours": [8, 9, 10, 11, 12, 13, 14, 15, 16],
        "wallet_prefix": "bc1q",
    },
    "romance_scammer": {
        "platforms": ["tinder", "facebook", "telegram", "whatsapp"],
        "timezone": "UTC+1",
        "active_hours": [18, 19, 20, 21, 22, 23, 0],
        "wallet_prefix": "T",
    },
    "mule_recruiter": {
        "platforms": ["telegram", "vkontakte", "signal", "discord"],
        "timezone": "UTC+5",
        "active_hours": [9, 10, 11, 13, 14, 15, 16, 17],
        "wallet_prefix": "0x",
    },
    "pan_clef_author": {
        "platforms": ["forum", "email", "blog", "research_archive"],
        "timezone": "UTC+0",
        "active_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17],
        "wallet_prefix": "0x",
    },
}


def register_actor_profile(profile: CriminalActorProfile) -> None:
    """Register profile in memory cache."""
    global _actor_profiles
    _actor_profiles[str(profile.actor_id)] = profile


def add_sample_to_actor(actor_id: str, text: str) -> dict:
    """Add a new text sample to a known actor, update their centroid fingerprint and graph."""
    global _actor_profiles
    profile = _actor_profiles.get(actor_id)
    if not profile:
        # Fallback to vectorstore record reconstruction
        from stylometry.vectorstore import get_actor
        rec = get_actor(actor_id)
        if rec:
            profile = CriminalActorProfile(
                actor_id=uuid.UUID(actor_id) if len(actor_id) == 36 else uuid.uuid4(),
                archetype=rec.metadata.get("archetype", "unknown"),
                handles=rec.metadata.get("handles", [rec.handle]),
                platforms=rec.metadata.get("platforms", [rec.platform]),
                timezone=rec.metadata.get("timezone", "UTC"),
                active_hours=rec.metadata.get("active_hours", []),
                wallet_addresses=rec.metadata.get("wallet_addresses", []),
            )
            _actor_profiles[actor_id] = profile
        else:
            raise ValueError(f"Actor {actor_id} not found in corpus")

    # Extract sample fingerprint
    sample_fp = extract_fingerprint(text)
    
    # Update profile metadata
    if not profile.linguistic_features:
        profile.linguistic_features = {}
    samples = profile.linguistic_features.get("samples", [])
    samples.append(text[:200])
    profile.linguistic_features["samples"] = samples
    profile.linguistic_features["sample_count"] = len(samples)

    # Re-calculate vector embedding in vector store
    from stylometry.vectorstore import get_actor
    rec = get_actor(actor_id)
    if rec is not None:
        # Exponential moving centroid
        updated_vec = 0.65 * rec.vector + 0.35 * sample_fp
        norm = float(np.linalg.norm(updated_vec))
        updated_vec = (updated_vec / (norm + 1e-9)).astype(np.float32)
    else:
        updated_vec = sample_fp

    primary_handle = profile.handles[0] if profile.handles else actor_id
    primary_platform = profile.platforms[0] if profile.platforms else "unknown"

    upsert_actor(
        actor_id=actor_id,
        handle=primary_handle,
        platform=primary_platform,
        vector=updated_vec,
        metadata={
            "archetype": profile.archetype,
            "timezone": profile.timezone,
            "handles": profile.handles,
            "platforms": profile.platforms,
            "wallet_addresses": profile.wallet_addresses,
            "sample_count": len(samples),
        },
    )

    # Update NetworkX graph
    add_actor_node(
        actor_id=actor_id,
        handle=primary_handle,
        platform=primary_platform,
        archetype=profile.archetype,
        metadata={"timezone": profile.timezone, "sample_count": len(samples)},
    )

    return {
        "actor_id": actor_id,
        "sample_count": len(samples),
        "handle": primary_handle,
        "status": "sample_indexed",
    }


def _generate_synthetic_actor(archetype: str, index: int) -> tuple[CriminalActorProfile, str]:
    """Generate a realistic synthetic CriminalActorProfile and a text sample."""
    meta = ARCHETYPE_METADATA[archetype]
    texts = ARCHETYPE_TEXT_CORPUS[archetype]
    text_sample = texts[index % len(texts)]
    
    actor_id = uuid.uuid4()
    base_handle = f"{archetype[:4]}_{random.choice(['boss', 'master', 'shadow', 'swift', 'vendor', 'net'])}_{index:02d}"
    handles = [f"@{base_handle}", f"{base_handle}_backup", f"{base_handle}_official"]
    wallets = [
        f"{meta['wallet_prefix']}{uuid.uuid4().hex[:32]}",
        f"{meta['wallet_prefix']}{uuid.uuid4().hex[:32]}",
    ]

    profile = CriminalActorProfile(
        actor_id=actor_id,
        archetype=archetype,
        handles=handles,
        platforms=meta["platforms"],
        timezone=meta["timezone"],
        active_hours=meta["active_hours"],
        wallet_addresses=wallets,
        linguistic_features={
            "primary_language": "en",
            "archetype": archetype,
            "sample_snippet": text_sample[:100],
        },
        transaction_features={
            "risk_score": 0.85 + (index % 10) * 0.01,
            "mixer_usage": archetype in ("darknet_vendor", "ransomware_operator"),
        },
        data_source="synthetic",
    )
    return profile, text_sample


def load_synthetic_corpus(n: int = 30) -> int:
    """Populate vectorstore and network graph with synthetic actor profiles."""
    global _actor_profiles
    archetypes = list(ARCHETYPE_TEXT_CORPUS.keys())
    
    all_texts: List[str] = []
    actor_items: List[tuple[CriminalActorProfile, str]] = []

    for i in range(n):
        arch = archetypes[i % len(archetypes)]
        profile, text = _generate_synthetic_actor(arch, i)
        actor_items.append((profile, text))
        all_texts.append(text)

    # Fit TF-IDF on corpus
    fit_tfidf(all_texts)

    # Upsert actors into vectorstore, graph, and profile registry
    previous_profile: Optional[CriminalActorProfile] = None
    for profile, text in actor_items:
        actor_id_str = str(profile.actor_id)
        _actor_profiles[actor_id_str] = profile
        
        # Extract fingerprint
        fp = extract_fingerprint(text)
        primary_handle = profile.handles[0] if profile.handles else actor_id_str
        primary_platform = profile.platforms[0] if profile.platforms else "unknown"

        upsert_actor(
            actor_id=actor_id_str,
            handle=primary_handle,
            platform=primary_platform,
            vector=fp,
            metadata={
                "archetype": profile.archetype,
                "timezone": profile.timezone,
                "handles": profile.handles,
                "platforms": profile.platforms,
                "wallet_addresses": profile.wallet_addresses,
            },
        )

        add_actor_node(
            actor_id=actor_id_str,
            handle=primary_handle,
            platform=primary_platform,
            archetype=profile.archetype,
            metadata={
                "timezone": profile.timezone,
                "wallets": profile.wallet_addresses,
            },
        )

        # Add some cross-actor edges for graph connectivity
        if previous_profile and previous_profile.archetype == profile.archetype:
            add_actor_edge(
                src_id=str(previous_profile.actor_id),
                dst_id=actor_id_str,
                edge_type="co_operation",
                weight=0.8,
            )
        previous_profile = profile

    logger.info("Loaded %d synthetic actor profiles into ShadowTrace corpus.", len(_actor_profiles))
    return len(_actor_profiles)


def get_actor_profile(actor_id: str) -> Optional[CriminalActorProfile]:
    """Retrieve full CriminalActorProfile by actor_id."""
    return _actor_profiles.get(actor_id)


def get_all_profiles() -> List[CriminalActorProfile]:
    """Return all loaded CriminalActorProfiles."""
    return list(_actor_profiles.values())


def load_from_path(path: str) -> int:
    """Optional loader for external json/csv datasets."""
    if not os.path.exists(path):
        logger.warning("Corpus path does not exist: %s", path)
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        if isinstance(data, list):
            for item in data:
                profile = CriminalActorProfile.model_validate(item)
                text = item.get("text_sample", item.get("text", ""))
                _actor_profiles[str(profile.actor_id)] = profile
                fp = extract_fingerprint(text) if text else extract_fingerprint(profile.archetype)
                upsert_actor(
                    actor_id=str(profile.actor_id),
                    handle=profile.handles[0] if profile.handles else str(profile.actor_id),
                    platform=profile.platforms[0] if profile.platforms else "unknown",
                    vector=fp,
                    metadata=profile.model_dump(mode="json"),
                )
                count += 1
        return count
    except Exception as exc:
        logger.error("Failed to load corpus from %s: %s", path, exc)
        return 0

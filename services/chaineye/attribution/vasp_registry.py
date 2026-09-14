"""
VASP (Virtual Asset Service Provider) & Entity Attribution Registry.
Maintains curated database of known exchange deposit addresses, hot wallets,
mixers, bridges, OTC desks, and known illicit clusters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EntityInfo:
    name: str
    category: str  # exchange, mixer, bridge, p2p, darknet, mule, illicit
    risk_score: float  # 0.0 (safe/regulated) to 1.0 (high risk/sanctioned)
    jurisdiction: str
    is_vasp: bool
    description: str


# Curated labeled addresses for BTC, ETH, and EVM chains
KNOWN_ENTITIES: dict[str, EntityInfo] = {
    # ── Exchanges / VASPs (Regulated / High Volume) ──────────────────────────
    "0x28c6c06298d514db089934071355e5743bf21d60": EntityInfo(
        name="Binance Hot Wallet 14",
        category="exchange",
        risk_score=0.15,
        jurisdiction="Global / Cayman Islands",
        is_vasp=True,
        description="Binance centralized hot wallet deposit/withdrawal pool",
    ),
    "0x71c83638379185a61142b19127765f14f0d6498b": EntityInfo(
        name="Binance Hot Wallet 6",
        category="exchange",
        risk_score=0.15,
        jurisdiction="Global",
        is_vasp=True,
        description="Binance high-throughput liquidity router",
    ),
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": EntityInfo(
        name="Binance Hot Wallet 8",
        category="exchange",
        risk_score=0.15,
        jurisdiction="Global",
        is_vasp=True,
        description="Binance ETH hot wallet",
    ),
    "0x503828976d22510aad0201ac7ec88293211d23da": EntityInfo(
        name="Coinbase Hot Wallet",
        category="exchange",
        risk_score=0.05,
        jurisdiction="United States (FinCEN Regulated)",
        is_vasp=True,
        description="Coinbase centralized exchange main custody address",
    ),
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": EntityInfo(
        name="Kraken Exchange 1",
        category="exchange",
        risk_score=0.10,
        jurisdiction="United States",
        is_vasp=True,
        description="Kraken exchange deposit gateway",
    ),
    "0xa929022c9107643515f5c777ce9a910f0d1e490c": EntityInfo(
        name="Huobi (HTX) Hot Wallet",
        category="exchange",
        risk_score=0.35,
        jurisdiction="Seychelles",
        is_vasp=True,
        description="HTX deposit processing address",
    ),
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": EntityInfo(
        name="Gate.io Hot Wallet",
        category="exchange",
        risk_score=0.30,
        jurisdiction="Cayman Islands",
        is_vasp=True,
        description="Gate.io exchange aggregation wallet",
    ),
    # ── Instant Non-KYC Exchangers (High Risk / Frequent Cashout Targets) ────
    "0x4c9edd5852cd905f086c759e8383e09bff1e68b3": EntityInfo(
        name="FixedFloat Hot Wallet",
        category="exchange",
        risk_score=0.78,
        jurisdiction="Offshore / Low-KYC",
        is_vasp=True,
        description="Automated instant cryptocurrency exchange without compulsory KYC",
    ),
    "0x68b22215ff74e3606bd5e6c1de8c2d68180c85f7": EntityInfo(
        name="ChangeNOW Liquidity Pool",
        category="exchange",
        risk_score=0.72,
        jurisdiction="Belize / Low-KYC",
        is_vasp=True,
        description="Non-custodial instant swap platform frequently targeted in peeling chains",
    ),
    # ── Privacy Protocols / Mixers (Sanctioned / High Risk) ──────────────────
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": EntityInfo(
        name="Tornado.Cash: 100 ETH Pool",
        category="mixer",
        risk_score=0.98,
        jurisdiction="OFAC Sanctioned / Decentralized",
        is_vasp=False,
        description="Zero-knowledge privacy pool on Ethereum (OFAC SDN List)",
    ),
    "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": EntityInfo(
        name="Tornado.Cash: 0.1 ETH Pool",
        category="mixer",
        risk_score=0.98,
        jurisdiction="OFAC Sanctioned / Decentralized",
        is_vasp=False,
        description="Tornado Cash 0.1 ETH anonymity pool",
    ),
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": EntityInfo(
        name="Tornado.Cash: 1 ETH Pool",
        category="mixer",
        risk_score=0.98,
        jurisdiction="OFAC Sanctioned / Decentralized",
        is_vasp=False,
        description="Tornado Cash 1 ETH anonymity pool",
    ),
    # ── Bitcoin Addresses (Curated) ──────────────────────────────────────────
    "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s": EntityInfo(
        name="Binance BTC Hot Wallet",
        category="exchange",
        risk_score=0.15,
        jurisdiction="Global",
        is_vasp=True,
        description="Binance Bitcoin main aggregation pool",
    ),
    "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo": EntityInfo(
        name="Binance Cold Storage BTC",
        category="exchange",
        risk_score=0.10,
        jurisdiction="Global",
        is_vasp=True,
        description="Binance 100k+ BTC cold reserve storage",
    ),
    "bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6": EntityInfo(
        name="FixedFloat BTC Pool",
        category="exchange",
        risk_score=0.78,
        jurisdiction="Offshore",
        is_vasp=True,
        description="FixedFloat automated swap gateway on Bitcoin",
    ),
    "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97": EntityInfo(
        name="Bitfinex BTC Cold Wallet",
        category="exchange",
        risk_score=0.20,
        jurisdiction="British Virgin Islands",
        is_vasp=True,
        description="Bitfinex cold storage wallet",
    ),
}

# Prefix and heuristic lookup patterns
KNOWN_PATTERNS = [
    ("tornado", EntityInfo("Tornado.Cash Contract", "mixer", 0.98, "OFAC Sanctioned", False, "Mixer contract")),
    ("binance", EntityInfo("Binance Associated Address", "exchange", 0.15, "Global", True, "Binance infrastructure")),
    ("fixedfloat", EntityInfo("FixedFloat Associated Address", "exchange", 0.78, "Offshore", True, "Instant exchanger")),
    ("changenow", EntityInfo("ChangeNOW Associated Address", "exchange", 0.72, "Offshore", True, "Instant exchanger")),
    ("coinbase", EntityInfo("Coinbase Associated Address", "exchange", 0.05, "USA", True, "Coinbase infrastructure")),
]


def get_vasp_attribution(address: str) -> Optional[EntityInfo]:
    """
    Looks up address in curated VASP database.
    Normalizes hex addresses to lowercase.
    """
    clean_addr = address.strip().lower()
    # 1. Exact match
    if clean_addr in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[clean_addr]

    # 2. Case-preserved match for BTC base58
    if address.strip() in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[address.strip()]

    # 3. Pattern match
    for pattern, info in KNOWN_PATTERNS:
        if pattern in clean_addr:
            return info

    return None


def get_risk_score(address: str) -> float:
    """Returns risk score 0.0 (low) - 1.0 (critical), default 0.5 for unknown."""
    info = get_vasp_attribution(address)
    if info:
        return info.risk_score
    return 0.50

"""
Multi-chain transaction explorer.
Fetches on-chain transaction history from Blockstream (Bitcoin) and Etherscan/Alchemy (EVM).
Includes deterministic mock fallback for offline development, tests, and demo environments.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from services.chaineye.attribution.vasp_registry import get_vasp_attribution

logger = logging.getLogger("chaineye.explorer")

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
ALCHEMY_API_KEY   = os.getenv("ALCHEMY_API_KEY", "")
BLOCKSTREAM_BASE  = "https://blockstream.info/api"
ETHERSCAN_BASE    = "https://api.etherscan.io/api"


@dataclass
class TransactionRecord:
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    amount_usd: float
    token: str  # "BTC", "ETH", "USDT", "MATIC"
    timestamp: datetime
    chain: str  # "bitcoin", "ethereum", "polygon"
    block_number: int = 0
    is_coinbase: bool = False
    co_inputs: list[str] = field(default_factory=list)


def detect_chain(address: str) -> str:
    """Infers blockchain network from address format."""
    addr = address.strip()
    if addr.startswith("0x") and len(addr) == 42:
        return "ethereum"
    if addr.startswith(("1", "3", "bc1")):
        return "bitcoin"
    return "ethereum"


async def fetch_address_transactions(
    address: str,
    chain: Optional[str] = None,
    depth: int = 3,
    max_tx: int = 50,
    http_client: Optional[httpx.AsyncClient] = None,
) -> list[TransactionRecord]:
    """
    Fetches transaction history for an address across multi-hop paths.
    Falls back to deterministic realistic mock transactions if APIs are unreachable or offline.
    """
    target_chain = chain or detect_chain(address)

    client = http_client or httpx.AsyncClient(timeout=15.0)
    try:
        if target_chain == "bitcoin":
            txs = await _fetch_blockstream_btc(address, max_tx, client)
            if txs:
                return txs
        elif target_chain in ("ethereum", "polygon") and ETHERSCAN_API_KEY:
            txs = await _fetch_etherscan_evm(address, target_chain, max_tx, client)
            if txs:
                return txs
    except Exception as e:
        logger.warning(f"Live blockchain API error for {address} on {target_chain}: {e}. Falling back to simulation.")
    finally:
        if http_client is None:
            await client.aclose()

    # Deterministic synthetic multi-hop trace generation
    return generate_mock_trace_flow(address, target_chain, depth=depth)


async def _fetch_blockstream_btc(
    address: str, max_tx: int, client: httpx.AsyncClient
) -> list[TransactionRecord]:
    url = f"{BLOCKSTREAM_BASE}/address/{address}/txs"
    resp = await client.get(url)
    if resp.status_code != 200:
        return []

    raw_txs = resp.json()[:max_tx]
    records: list[TransactionRecord] = []
    btc_price_usd = 65000.0

    for tx in raw_txs:
        tx_hash = tx.get("txid", "")
        status = tx.get("status", {})
        block_time = status.get("block_time")
        ts = datetime.fromtimestamp(block_time, tz=timezone.utc) if block_time else datetime.now(timezone.utc)
        block_num = status.get("block_height", 0)

        # Extract all input addresses for co-spend analysis
        inputs = [
            vin.get("prevout", {}).get("scriptpubkey_address", "")
            for vin in tx.get("vin", [])
            if vin.get("prevout", {}).get("scriptpubkey_address")
        ]
        from_addr = inputs[0] if inputs else "coinbase"

        for vout in tx.get("vout", []):
            to_addr = vout.get("scriptpubkey_address")
            if not to_addr:
                continue
            satoshis = vout.get("value", 0)
            btc_val = satoshis / 1e8
            records.append(
                TransactionRecord(
                    tx_hash=tx_hash,
                    from_address=from_addr,
                    to_address=to_addr,
                    amount=btc_val,
                    amount_usd=btc_val * btc_price_usd,
                    token="BTC",
                    timestamp=ts,
                    chain="bitcoin",
                    block_number=block_num,
                    co_inputs=inputs,
                )
            )

    return records


async def _fetch_etherscan_evm(
    address: str, chain: str, max_tx: int, client: httpx.AsyncClient
) -> list[TransactionRecord]:
    url = f"{ETHERSCAN_BASE}?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset={max_tx}&sort=desc&apikey={ETHERSCAN_API_KEY}"
    resp = await client.get(url)
    if resp.status_code != 200:
        return []

    data = resp.json()
    if data.get("status") != "1" or not isinstance(data.get("result"), list):
        return []

    records: list[TransactionRecord] = []
    eth_price_usd = 3500.0

    for item in data["result"]:
        tx_hash = item.get("hash", "")
        from_addr = item.get("from", "").lower()
        to_addr = item.get("to", "").lower()
        value_wei = int(item.get("value", 0))
        eth_val = value_wei / 1e18
        ts_int = int(item.get("timeStamp", 0))
        ts = datetime.fromtimestamp(ts_int, tz=timezone.utc) if ts_int else datetime.now(timezone.utc)
        block_num = int(item.get("blockNumber", 0))

        records.append(
            TransactionRecord(
                tx_hash=tx_hash,
                from_address=from_addr,
                to_address=to_addr,
                amount=eth_val,
                amount_usd=eth_val * eth_price_usd,
                token="ETH" if chain == "ethereum" else "MATIC",
                timestamp=ts,
                chain=chain,
                block_number=block_num,
            )
        )

    return records


def generate_mock_trace_flow(root_address: str, chain: str = "ethereum", depth: int = 3) -> list[TransactionRecord]:
    """
    Generates deterministic, realistic multi-hop criminal transaction flows:
    Target Address -> Intermediate Peeling/Mule Addresses -> High-Risk Mixer / Low-KYC VASP -> Centralized Exchange Cashout.
    """
    seed = int(hashlib.sha256(root_address.encode()).hexdigest()[:8], 16)
    records: list[TransactionRecord] = []

    now = datetime.now(timezone.utc)
    unit_token = "BTC" if chain == "bitcoin" else "ETH"
    unit_price = 65000.0 if chain == "bitcoin" else 3500.0

    current_addrs = [root_address]
    initial_volume = 15.5 + (seed % 100) * 0.25  # ~15-40 ETH or ~1-3 BTC

    # Intermediate hop entity names / addresses
    if chain == "bitcoin":
        destinations = [
            "bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6",  # FixedFloat
            "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s",          # Binance BTC
        ]
    else:
        destinations = [
            "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",  # Tornado Cash
            "0x4c9edd5852cd905f086c759e8383e09bff1e68b3",  # FixedFloat
            "0x71c83638379185a61142b19127765f14f0d6498b",  # Binance Hot Wallet 6
        ]

    for hop in range(1, depth + 1):
        next_addrs = []
        for idx, src in enumerate(current_addrs):
            # Split into peeling payment + change / mule address
            peel_amount = initial_volume * (0.65 / hop)
            change_amount = initial_volume * (0.35 / hop)

            # Generate deterministic intermediate address or final VASP destination
            if hop == depth:
                dest_addr = destinations[(seed + hop + idx) % len(destinations)]
            else:
                dest_addr = f"0x{hashlib.sha256(f'{src}_{hop}_peel'.encode()).hexdigest()[:40]}" if chain != "bitcoin" else f"bc1q{hashlib.sha256(f'{src}_{hop}_peel'.encode()).hexdigest()[:38]}"
            
            change_addr = f"0x{hashlib.sha256(f'{src}_{hop}_change'.encode()).hexdigest()[:40]}" if chain != "bitcoin" else f"bc1q{hashlib.sha256(f'{src}_{hop}_change'.encode()).hexdigest()[:38]}"

            tx_hash_peel = f"0x{hashlib.sha256(f'tx_{src}_{dest_addr}_{hop}'.encode()).hexdigest()}"
            tx_hash_change = f"0x{hashlib.sha256(f'tx_{src}_{change_addr}_{hop}'.encode()).hexdigest()}"

            # Peeling transfer
            records.append(
                TransactionRecord(
                    tx_hash=tx_hash_peel,
                    from_address=src,
                    to_address=dest_addr,
                    amount=round(peel_amount, 4),
                    amount_usd=round(peel_amount * unit_price, 2),
                    token=unit_token,
                    timestamp=now,
                    chain=chain,
                    block_number=19000000 + hop * 100,
                    co_inputs=[src, f"{src}_sub1"] if chain == "bitcoin" else [],
                )
            )

            # Change transfer
            records.append(
                TransactionRecord(
                    tx_hash=tx_hash_change,
                    from_address=src,
                    to_address=change_addr,
                    amount=round(change_amount, 4),
                    amount_usd=round(change_amount * unit_price, 2),
                    token=unit_token,
                    timestamp=now,
                    chain=chain,
                    block_number=19000000 + hop * 100 + 1,
                    co_inputs=[src] if chain == "bitcoin" else [],
                )
            )

            next_addrs.append(change_addr)

        current_addrs = next_addrs[:2]  # Keep graph branching bounded

    return records

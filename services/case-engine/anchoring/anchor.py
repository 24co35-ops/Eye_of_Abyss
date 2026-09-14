"""
Blockchain and IPFS anchoring module for Eye of Abyss.
Implements the full Evidence Registry flow from design-doc.md §4:
  1. Pin canonical evidence JSON to IPFS (via Pinata REST API) -> returns CID.
  2. Compute canonical SHA-256 hash of evidence object -> returns 0x... and bytes32.
  3. Submit hash + case_id + module_id + CID to EvidenceRegistry smart contract on Polygon -> returns tx_hash.
  4. Query on-chain verification status.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, TransactionNotFound
except ImportError:
    class ContractLogicError(Exception):  # type: ignore
        pass

    class TransactionNotFound(Exception):  # type: ignore
        pass

    class Web3:  # type: ignore
        @staticmethod
        def to_checksum_address(addr: str) -> str:
            return addr

        class HTTPProvider:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

logger = logging.getLogger("case_engine.anchoring")

# Configuration from environment
EVIDENCE_REGISTRY_ADDRESS = os.getenv("EVIDENCE_REGISTRY_ADDRESS", "")
POLYGON_RPC_URL           = os.getenv("POLYGON_RPC_URL", "https://rpc-mumbai.maticvigil.com")
PRIVATE_KEY               = os.getenv("PRIVATE_KEY", "")
PINATA_API_KEY            = os.getenv("PINATA_API_KEY", "")
PINATA_SECRET_KEY         = os.getenv("PINATA_SECRET_KEY", "")
PINATA_JWT                = os.getenv("PINATA_JWT", "")

PINATA_PIN_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

# ABI for EvidenceRegistry.sol
EVIDENCE_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"},
            {"internalType": "string", "name": "caseId", "type": "string"},
            {"internalType": "string", "name": "moduleId", "type": "string"},
            {"internalType": "string", "name": "ipfsCid", "type": "string"},
        ],
        "name": "anchor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"}
        ],
        "name": "verify",
        "outputs": [
            {"internalType": "bool", "name": "isAnchored", "type": "bool"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"}
        ],
        "name": "records",
        "outputs": [
            {"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "submittedBy", "type": "address"},
            {"internalType": "string", "name": "caseId", "type": "string"},
            {"internalType": "string", "name": "moduleId", "type": "string"},
            {"internalType": "string", "name": "ipfsCid", "type": "string"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "name": "caseEvidence",
        "outputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"},
            {"indexed": False, "internalType": "string", "name": "caseId", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "moduleId", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "name": "EvidenceAnchored",
        "type": "event",
    },
]


def serialize_canonical_json(data: Any) -> bytes:
    """Serializes data to canonical JSON (sorted keys, compact separators, UUID/datetime converted)."""
    def _default(o: Any) -> Any:
        if isinstance(o, (UUID, datetime)):
            return str(o)
        if hasattr(o, "model_dump"):
            return o.model_dump(mode="json")
        if hasattr(o, "dict"):
            return o.dict()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    if hasattr(data, "model_dump"):
        data_dict = data.model_dump(mode="json")
    elif hasattr(data, "dict"):
        data_dict = data.dict()
    else:
        data_dict = data

    return json.dumps(data_dict, sort_keys=True, separators=(",", ":"), default=_default).encode("utf-8")


def compute_evidence_hash(data: Any) -> tuple[str, bytes]:
    """
    Computes deterministic SHA-256 hash of the evidence object.
    Returns tuple: (hex_str_with_0x_prefix, 32_raw_bytes).
    """
    raw = serialize_canonical_json(data)
    digest = hashlib.sha256(raw).digest()
    hex_str = "0x" + digest.hex()
    return hex_str, digest


async def pin_to_pinata(
    evidence_dict: dict,
    name: Optional[str] = None,
    jwt_token: Optional[str] = None,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> str:
    """
    Pins canonical evidence JSON to IPFS using Pinata REST API.
    Returns the IPFS CID (IpfsHash).
    """
    jwt = jwt_token or PINATA_JWT
    key = api_key or PINATA_API_KEY
    sec = secret_key or PINATA_SECRET_KEY

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if jwt:
        headers["Authorization"] = f"Bearer {jwt}"
    elif key and sec:
        headers["pinata_api_key"] = key
        headers["pinata_secret_api_key"] = sec
    else:
        # Fallback for offline dev / testing when credentials are not configured
        logger.warning("Pinata credentials not set — generating deterministic mock CID.")
        ev_hash, _ = compute_evidence_hash(evidence_dict)
        return f"QmStub{ev_hash[2:42]}"

    ev_id = str(evidence_dict.get("evidence_id", "unknown"))
    case_id = str(evidence_dict.get("case_id", ""))
    module_id = str(evidence_dict.get("module_id", ""))

    payload = {
        "pinataContent": evidence_dict,
        "pinataMetadata": {
            "name": name or f"evidence-{ev_id}",
            "keyvalues": {
                "case_id": case_id,
                "module_id": module_id,
            },
        },
        "pinataOptions": {
            "cidVersion": 1,
        },
    }

    client = http_client or httpx.AsyncClient(timeout=30.0)
    try:
        response = await client.post(PINATA_PIN_JSON_URL, json=payload, headers=headers)
        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Pinata IPFS pinning failed with HTTP {response.status_code}: {response.text}"
            )
        data = response.json()
        cid = data.get("IpfsHash")
        if not cid:
            raise ValueError(f"Pinata response missing 'IpfsHash': {data}")
        return cid
    finally:
        if http_client is None:
            await client.aclose()


def anchor_evidence_onchain(
    evidence_hash_hex: str,
    case_id: str,
    module_id: str,
    ipfs_cid: str,
    rpc_url: Optional[str] = None,
    private_key: Optional[str] = None,
    contract_address: Optional[str] = None,
    w3_instance: Optional[Web3] = None,
) -> str:
    """
    Submits evidence hash, case_id, module_id, and ipfs_cid to Polygon EvidenceRegistry smart contract.
    Returns transaction hash hex string (0x...).
    """
    rpc = rpc_url or POLYGON_RPC_URL
    pk = private_key or PRIVATE_KEY
    addr = contract_address or EVIDENCE_REGISTRY_ADDRESS

    if not pk or not addr:
        logger.warning("Blockchain credentials/address not configured — returning mock tx hash.")
        return f"0xmock{evidence_hash_hex[2:34]}{int(datetime.now(timezone.utc).timestamp()):x}"

    w3 = w3_instance or Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        raise ConnectionError(f"Could not connect to Polygon RPC endpoint: {rpc}")

    account = w3.eth.account.from_key(pk)
    checksum_contract_addr = Web3.to_checksum_address(addr)
    contract = w3.eth.contract(address=checksum_contract_addr, abi=EVIDENCE_REGISTRY_ABI)

    # Normalize hash to 32 bytes
    clean_hex = evidence_hash_hex.removeprefix("0x")
    if len(clean_hex) != 64:
        raise ValueError(f"Invalid SHA-256 hash length: {evidence_hash_hex}")
    bytes32_hash = bytes.fromhex(clean_hex)

    # Prepare transaction parameters
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    chain_id = w3.eth.chain_id
    gas_price = w3.eth.gas_price

    tx_function = contract.functions.anchor(
        bytes32_hash,
        str(case_id),
        str(module_id),
        str(ipfs_cid),
    )

    try:
        estimated_gas = tx_function.estimate_gas({"from": account.address})
        gas_limit = int(estimated_gas * 1.25)
    except Exception:
        gas_limit = 250_000

    tx_data = tx_function.build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": gas_limit,
        "gasPrice": gas_price,
        "chainId": chain_id,
    })

    signed_tx = w3.eth.account.sign_transaction(tx_data, private_key=pk)
    raw_tx = getattr(signed_tx, "raw_transaction", None) or getattr(signed_tx, "rawTransaction")
    tx_hash_bytes = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=120)

    raw_tx_hash = receipt.get("transactionHash")
    if hasattr(raw_tx_hash, "to_0x_hex"):
        tx_hash_hex = raw_tx_hash.to_0x_hex()
    elif hasattr(raw_tx_hash, "hex"):
        h = raw_tx_hash.hex()
        tx_hash_hex = h if h.startswith("0x") else "0x" + h
    elif isinstance(raw_tx_hash, str):
        tx_hash_hex = raw_tx_hash if raw_tx_hash.startswith("0x") else "0x" + raw_tx_hash
    else:
        tx_hash_hex = str(raw_tx_hash)

    if receipt.get("status") != 1:
        raise RuntimeError(f"On-chain anchoring transaction reverted! Tx: {tx_hash_hex}")

    return tx_hash_hex


def verify_evidence_onchain(
    evidence_hash_hex: str,
    rpc_url: Optional[str] = None,
    contract_address: Optional[str] = None,
    w3_instance: Optional[Web3] = None,
) -> dict[str, Any]:
    """
    Verifies if evidence hash is anchored in the EvidenceRegistry contract.
    Returns dict: {"is_anchored": bool, "timestamp": int, "datetime": Optional[str]}
    """
    rpc = rpc_url or POLYGON_RPC_URL
    addr = contract_address or EVIDENCE_REGISTRY_ADDRESS

    if not addr:
        return {"is_anchored": False, "timestamp": 0, "datetime": None, "note": "Contract address not configured"}

    w3 = w3_instance or Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        raise ConnectionError(f"Could not connect to Polygon RPC endpoint: {rpc}")

    checksum_contract_addr = Web3.to_checksum_address(addr)
    contract = w3.eth.contract(address=checksum_contract_addr, abi=EVIDENCE_REGISTRY_ABI)

    clean_hex = evidence_hash_hex.removeprefix("0x")
    bytes32_hash = bytes.fromhex(clean_hex)

    is_anchored, ts = contract.functions.verify(bytes32_hash).call()
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts > 0 else None

    return {
        "is_anchored": is_anchored,
        "timestamp": ts,
        "datetime": dt,
        "evidence_hash": evidence_hash_hex,
    }


async def anchor_evidence(
    evidence_data: Any,
    db_session: Optional[Any] = None,
    rpc_url: Optional[str] = None,
    private_key: Optional[str] = None,
    contract_address: Optional[str] = None,
    jwt_token: Optional[str] = None,
    http_client: Optional[httpx.AsyncClient] = None,
    w3_instance: Optional[Web3] = None,
) -> dict[str, Any]:
    """
    Executes the complete end-to-end evidence anchoring flow:
      1. Pins canonical JSON to IPFS (via Pinata) -> CID
      2. Computes SHA-256 hash -> hex hash & bytes32
      3. Calls EvidenceRegistry.anchor() on Polygon -> tx_hash
      4. Optionally updates Database Evidence record
      5. Returns result dictionary.
    """
    # 1. Prepare dictionary representation
    if hasattr(evidence_data, "model_dump"):
        ev_dict = evidence_data.model_dump(mode="json")
    elif hasattr(evidence_data, "dict"):
        ev_dict = evidence_data.dict()
    elif isinstance(evidence_data, dict):
        ev_dict = dict(evidence_data)
    else:
        raise TypeError(f"Unsupported evidence_data type: {type(evidence_data).__name__}")

    case_id = str(ev_dict.get("case_id", ""))
    module_id = str(ev_dict.get("module_id", ""))
    evidence_id = str(ev_dict.get("evidence_id", ""))

    # 2. Pin to IPFS via Pinata
    ipfs_cid = await pin_to_pinata(
        ev_dict,
        name=f"evidence-{evidence_id}",
        jwt_token=jwt_token,
        http_client=http_client,
    )

    # 3. Compute deterministic canonical SHA-256 hash
    ev_hash_hex, _ = compute_evidence_hash(ev_dict)

    # 4. Anchor on Polygon
    tx_hash = anchor_evidence_onchain(
        evidence_hash_hex=ev_hash_hex,
        case_id=case_id,
        module_id=module_id,
        ipfs_cid=ipfs_cid,
        rpc_url=rpc_url,
        private_key=private_key,
        contract_address=contract_address,
        w3_instance=w3_instance,
    )

    # 5. Update DB if session provided
    if db_session is not None:
        try:
            try:
                from db import Evidence
            except ImportError:
                from services.case_engine.db import Evidence
            from sqlalchemy import select

            uid = UUID(evidence_id) if isinstance(evidence_id, str) else evidence_id
            stmt = select(Evidence).where(Evidence.evidence_id == uid)
            row = (await db_session.execute(stmt)).scalar_one_or_none()
            if row:
                row.chain_anchor = tx_hash
                row.ipfs_cid = ipfs_cid
                row.hash_sha256 = ev_hash_hex
                await db_session.commit()
        except Exception as e:
            logger.error(f"Failed to update database evidence record {evidence_id}: {e}")

    return {
        "evidence_id": evidence_id,
        "case_id": case_id,
        "module_id": module_id,
        "hash_sha256": ev_hash_hex,
        "ipfs_cid": ipfs_cid,
        "tx_hash": tx_hash,
    }

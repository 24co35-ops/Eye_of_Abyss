"""
Unit tests for Case Engine Evidence Registry anchoring flow.
Tests SHA-256 hash calculation, mock Pinata IPFS pinning, and mock Polygon Web3 contract calls.
"""

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from hexbytes import HexBytes

import os
import sys
from pathlib import Path

# Add project root and case-engine dir to path
_ROOT = Path(__file__).resolve().parents[3]
_CASE_ENGINE = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_CASE_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CASE_ENGINE))

from shared.schemas import Artifact, EvidenceObject
from anchoring.anchor import (
    EVIDENCE_REGISTRY_ABI,
    anchor_evidence,
    anchor_evidence_onchain,
    compute_evidence_hash,
    pin_to_pinata,
    serialize_canonical_json,
    verify_evidence_onchain,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_evidence():
    case_id = uuid4()
    evidence_id = uuid4()
    return EvidenceObject(
        evidence_id=evidence_id,
        case_id=case_id,
        module_id="voiceguard",
        verdict="Synthetic voice detected (TTS model)",
        verdict_code="SYNTHETIC_TTS",
        confidence=0.94,
        confidence_tier="high",
        payload={"tts_model": "ElevenLabs-v2", "pitch_variance": 0.012},
        artifacts=[
            Artifact(filename="mfcc_heatmap.png", file_type="image/png", description="MFCC feature map"),
            Artifact(filename="spectrogram.png", file_type="image/png", description="Mel spectrogram"),
        ],
        submitted_by="OFFICER_042",
        created_by="OFFICER_042",
    )


# ── Test 1: Canonical SHA-256 Hash Computation ────────────────────────────────

def test_compute_evidence_hash_deterministic(sample_evidence):
    """Verifies that canonical JSON serialization produces deterministic hashes regardless of key order."""
    dict_a = {
        "case_id": str(sample_evidence.case_id),
        "module_id": "voiceguard",
        "verdict": "Synthetic voice detected",
        "confidence": 0.94,
        "payload": {"a": 1, "b": 2},
    }
    dict_b = {
        "payload": {"b": 2, "a": 1},
        "confidence": 0.94,
        "verdict": "Synthetic voice detected",
        "module_id": "voiceguard",
        "case_id": str(sample_evidence.case_id),
    }

    hex_a, bytes_a = compute_evidence_hash(dict_a)
    hex_b, bytes_b = compute_evidence_hash(dict_b)

    assert hex_a == hex_b
    assert bytes_a == bytes_b
    assert hex_a.startswith("0x")
    assert len(hex_a) == 66  # "0x" + 64 hex characters
    assert len(bytes_a) == 32


def test_compute_evidence_hash_pydantic(sample_evidence):
    """Tests hash computation directly on Pydantic EvidenceObject."""
    hex_hash, raw_bytes = compute_evidence_hash(sample_evidence)
    assert hex_hash.startswith("0x")
    assert len(raw_bytes) == 32

    # Verify matching raw SHA-256
    raw_serialized = serialize_canonical_json(sample_evidence)
    expected_digest = hashlib.sha256(raw_serialized).digest()
    assert raw_bytes == expected_digest


# ── Test 2: Pinata IPFS Pinning (Mocked HTTP) ─────────────────────────────────

@pytest.mark.asyncio
async def test_pin_to_pinata_with_jwt():
    """Verifies Pinata IPFS pinning using JWT bearer token."""
    mock_cid = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"
    test_dict = {"case_id": "test-case-123", "module_id": "chaineye", "data": "sample"}

    async def mock_handler(request: httpx.Request):
        assert request.url == "https://api.pinata.cloud/pinning/pinJSONToIPFS"
        assert request.headers["Authorization"] == "Bearer test_jwt_token_secret"
        body = json.loads(request.content.decode())
        assert body["pinataContent"]["case_id"] == "test-case-123"
        assert body["pinataMetadata"]["keyvalues"]["module_id"] == "chaineye"
        return httpx.Response(200, json={"IpfsHash": mock_cid, "PinSize": 1234, "Timestamp": "2026-09-14T10:00:00Z"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        cid = await pin_to_pinata(
            test_dict,
            jwt_token="test_jwt_token_secret",
            http_client=client,
        )

    assert cid == mock_cid


@pytest.mark.asyncio
async def test_pin_to_pinata_with_api_keys():
    """Verifies Pinata IPFS pinning using API Key & Secret Key headers."""
    mock_cid = "bafybeic5678mockcidstringforipfsregistryflow"
    test_dict = {"case_id": "test-case-456", "module_id": "shadowtrace"}

    async def mock_handler(request: httpx.Request):
        assert request.headers["pinata_api_key"] == "MY_PINATA_KEY"
        assert request.headers["pinata_secret_api_key"] == "MY_PINATA_SECRET"
        return httpx.Response(200, json={"IpfsHash": mock_cid})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        cid = await pin_to_pinata(
            test_dict,
            api_key="MY_PINATA_KEY",
            secret_key="MY_PINATA_SECRET",
            http_client=client,
        )

    assert cid == mock_cid


@pytest.mark.asyncio
async def test_pin_to_pinata_error_handling():
    """Verifies that HTTP errors from Pinata raise an informative RuntimeError."""
    test_dict = {"case_id": "test-case-error"}

    async def mock_handler(request: httpx.Request):
        return httpx.Response(401, json={"error": "Unauthorized API key"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(RuntimeError) as exc_info:
            await pin_to_pinata(
                test_dict,
                jwt_token="invalid_token",
                http_client=client,
            )

    assert "HTTP 401" in str(exc_info.value)


# ── Test 3: Web3 Polygon Contract Anchoring (Mocked Web3) ─────────────────────

def test_anchor_evidence_onchain_success():
    """Verifies Web3 contract call to EvidenceRegistry.anchor()."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 80001
    mock_w3.eth.gas_price = 25000000000
    mock_w3.eth.get_transaction_count.return_value = 5

    # Mock account
    mock_account = MagicMock()
    mock_account.address = "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
    mock_w3.eth.account.from_key.return_value = mock_account

    # Mock contract & function
    mock_contract = MagicMock()
    mock_tx_func = MagicMock()
    mock_tx_func.estimate_gas.return_value = 120_000
    mock_tx_func.build_transaction.return_value = {
        "from": mock_account.address,
        "nonce": 5,
        "gas": 150_000,
        "gasPrice": 25000000000,
        "chainId": 80001,
    }
    mock_contract.functions.anchor.return_value = mock_tx_func
    mock_w3.eth.contract.return_value = mock_contract

    # Mock signing & broadcast
    mock_signed = MagicMock()
    mock_signed.raw_transaction = b"\x01\x02\x03\x04"
    mock_w3.eth.account.sign_transaction.return_value = mock_signed

    expected_tx_hash = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    mock_w3.eth.send_raw_transaction.return_value = HexBytes(expected_tx_hash)
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "transactionHash": HexBytes(expected_tx_hash),
        "blockNumber": 42000000,
    }

    test_hash = "0x" + "aa" * 32
    case_id = "test-case-uuid"
    module_id = "voiceguard"
    cid = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"

    tx_hash = anchor_evidence_onchain(
        evidence_hash_hex=test_hash,
        case_id=case_id,
        module_id=module_id,
        ipfs_cid=cid,
        rpc_url="https://rpc-mumbai.maticvigil.com",
        private_key="0x" + "11" * 32,
        contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        w3_instance=mock_w3,
    )

    assert tx_hash == expected_tx_hash
    # Verify contract function was called with exact arguments
    expected_bytes32 = bytes.fromhex("aa" * 32)
    mock_contract.functions.anchor.assert_called_once_with(
        expected_bytes32,
        case_id,
        module_id,
        cid,
    )


def test_anchor_evidence_onchain_reverted():
    """Verifies that an on-chain transaction revert raises RuntimeError."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.account.from_key.return_value = MagicMock(address="0x1234567890123456789012345678901234567890")
    
    mock_contract = MagicMock()
    mock_contract.functions.anchor.return_value.estimate_gas.return_value = 100_000
    mock_contract.functions.anchor.return_value.build_transaction.return_value = {}
    mock_w3.eth.contract.return_value = mock_contract
    mock_w3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"\x00")
    mock_w3.eth.send_raw_transaction.return_value = HexBytes("0x9999")
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 0,  # Reverted!
        "transactionHash": HexBytes("0x9999"),
    }

    with pytest.raises(RuntimeError) as exc_info:
        anchor_evidence_onchain(
            evidence_hash_hex="0x" + "bb" * 32,
            case_id="case-1",
            module_id="voiceguard",
            ipfs_cid="QmTest",
            private_key="0x" + "22" * 32,
            contract_address="0x1234567890123456789012345678901234567890",
            w3_instance=mock_w3,
        )

    assert "reverted" in str(exc_info.value)


# ── Test 4: On-Chain Verification ─────────────────────────────────────────────

def test_verify_evidence_onchain():
    """Verifies that verify_evidence_onchain queries EvidenceRegistry.verify() correctly."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True

    mock_contract = MagicMock()
    # Contract returns (is_anchored, timestamp)
    mock_contract.functions.verify.return_value.call.return_value = (True, 1726315200)
    mock_w3.eth.contract.return_value = mock_contract

    test_hash = "0x" + "cc" * 32
    res = verify_evidence_onchain(
        evidence_hash_hex=test_hash,
        contract_address="0x1234567890123456789012345678901234567890",
        w3_instance=mock_w3,
    )

    assert res["is_anchored"] is True
    assert res["timestamp"] == 1726315200
    assert "2024" in res["datetime"] or "2026" in res["datetime"]
    mock_contract.functions.verify.assert_called_once_with(bytes.fromhex("cc" * 32))


# ── Test 5: Full End-to-End Anchoring Flow ─────────────────────────────────────

@pytest.mark.asyncio
async def test_full_anchor_evidence_flow(sample_evidence):
    """Tests the full orchestration: Pinata pinning -> Canonical SHA-256 -> Web3 Polygon anchoring."""
    expected_cid = "QmFullPipelineCID1234567890abcdef"
    expected_tx_hash = "0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba"

    # Mock Pinata HTTP handler
    async def mock_pinata_handler(request: httpx.Request):
        return httpx.Response(200, json={"IpfsHash": expected_cid})

    transport = httpx.MockTransport(mock_pinata_handler)

    # Mock Web3
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.account.from_key.return_value = MagicMock(address="0x1111111111111111111111111111111111111111")
    mock_contract = MagicMock()
    mock_contract.functions.anchor.return_value.estimate_gas.return_value = 100_000
    mock_contract.functions.anchor.return_value.build_transaction.return_value = {}
    mock_w3.eth.contract.return_value = mock_contract
    mock_w3.eth.account.sign_transaction.return_value = MagicMock(raw_transaction=b"\x00")
    mock_w3.eth.send_raw_transaction.return_value = HexBytes(expected_tx_hash)
    mock_w3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "transactionHash": HexBytes(expected_tx_hash),
    }

    async with httpx.AsyncClient(transport=transport) as http_client:
        result = await anchor_evidence(
            evidence_data=sample_evidence,
            jwt_token="mock_jwt_token",
            private_key="0x" + "33" * 32,
            contract_address="0x2222222222222222222222222222222222222222",
            http_client=http_client,
            w3_instance=mock_w3,
        )

    assert result["evidence_id"] == str(sample_evidence.evidence_id)
    assert result["case_id"] == str(sample_evidence.case_id)
    assert result["module_id"] == "voiceguard"
    assert result["ipfs_cid"] == expected_cid
    assert result["tx_hash"] == expected_tx_hash
    assert result["hash_sha256"].startswith("0x")
    assert len(result["hash_sha256"]) == 66


@pytest.mark.asyncio
async def test_pin_to_pinata_fallback_no_creds():
    """Verifies that missing credentials produce a deterministic mock CID without throwing unhandled exceptions."""
    with patch.dict(os.environ, {"PINATA_JWT": "", "PINATA_API_KEY": "", "PINATA_SECRET_KEY": ""}):
        cid = await pin_to_pinata({"case_id": "c1", "data": "val"})
        assert cid.startswith("QmStub")


def test_anchor_onchain_fallback_no_creds():
    """Verifies fallback mock transaction hash when blockchain credentials are not configured."""
    with patch.dict(os.environ, {"PRIVATE_KEY": "", "EVIDENCE_REGISTRY_ADDRESS": ""}):
        tx = anchor_evidence_onchain(
            evidence_hash_hex="0x" + "ff" * 32,
            case_id="case-no-creds",
            module_id="voiceguard",
            ipfs_cid="QmStub123",
            private_key="",
            contract_address="",
        )
        assert tx.startswith("0xmock")


def test_verify_onchain_no_address():
    """Verifies verify_evidence_onchain returns unanchored status if contract address is missing."""
    with patch.dict(os.environ, {"EVIDENCE_REGISTRY_ADDRESS": ""}):
        res = verify_evidence_onchain("0x" + "ee" * 32, contract_address="")
        assert res["is_anchored"] is False
        assert res["timestamp"] == 0


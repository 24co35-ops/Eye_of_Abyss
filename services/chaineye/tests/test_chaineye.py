"""
Comprehensive test suite for ChainEye Forensics Service.
Tests VASP attribution, explorer, heuristics, GNN classification, XGBoost prediction,
FastAPI endpoints, and EvidenceObject generation.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

# Setup sys.path
_ROOT = Path(__file__).resolve().parents[3]
_SHARED = _ROOT / "shared"
_CHAINEYE = Path(__file__).resolve().parents[1]

for p in (str(_ROOT), str(_SHARED), str(_CHAINEYE)):
    if p not in sys.path:
        sys.path.insert(0, p)

from shared.schemas import EvidenceObject
from services.chaineye.attribution.vasp_registry import (
    KNOWN_ENTITIES,
    get_risk_score,
    get_vasp_attribution,
)
from services.chaineye.gnn.inference import extract_node_features_16dim, gnn_service
from services.chaineye.graph.builder import build_transaction_graph, export_cytoscape_json
from services.chaineye.graph.clustering import (
    DisjointSet,
    apply_cospend_heuristic,
    cluster_wallet_network,
    detect_peeling_chains,
)
from services.chaineye.graph.explorer import (
    TransactionRecord,
    detect_chain,
    fetch_address_transactions,
    generate_mock_trace_flow,
)
from services.chaineye.main import app
from services.chaineye.prediction.features import extract_withdrawal_features
from services.chaineye.prediction.model import withdrawal_predictor
from services.chaineye.synthetic.generator import generate_synthetic_actor_flow


# ── Fixtures & Client ─────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_wallet():
    return "0x71C83638379185a61142b19127765F14f0D6498B"


@pytest.fixture
def sample_transactions(sample_wallet):
    return generate_mock_trace_flow(sample_wallet, chain="ethereum", depth=3)


# ── Test 1: VASP Registry Attribution ─────────────────────────────────────────

def test_vasp_attribution_exact_match():
    # Binance hot wallet 6
    addr = "0x71c83638379185a61142b19127765f14f0d6498b"
    info = get_vasp_attribution(addr)
    assert info is not None
    assert "Binance" in info.name
    assert info.category == "exchange"
    assert info.is_vasp is True
    assert get_risk_score(addr) == 0.15


def test_vasp_attribution_mixer_sanctioned():
    # Tornado Cash 100 ETH
    addr = "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"
    info = get_vasp_attribution(addr)
    assert info is not None
    assert "Tornado" in info.name
    assert info.category == "mixer"
    assert info.risk_score >= 0.95


def test_vasp_attribution_unknown():
    addr = "0x1111111111111111111111111111111111111111"
    info = get_vasp_attribution(addr)
    assert info is None
    assert get_risk_score(addr) == 0.50


# ── Test 2: Multi-chain Explorer ──────────────────────────────────────────────

def test_detect_chain():
    assert detect_chain("0x71C83638379185a61142b19127765F14f0D6498B") == "ethereum"
    assert detect_chain("1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s") == "bitcoin"
    assert detect_chain("bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6") == "bitcoin"


@pytest.mark.asyncio
async def test_fetch_address_transactions_mock(sample_wallet):
    txs = await fetch_address_transactions(sample_wallet, chain="ethereum", depth=3)
    assert len(txs) > 0
    assert any(tx.from_address == sample_wallet for tx in txs)
    assert all(tx.amount_usd > 0 for tx in txs)


# ── Test 3: Heuristic Clustering ──────────────────────────────────────────────

def test_cospend_heuristic():
    ds = DisjointSet()
    tx = TransactionRecord(
        tx_hash="0x123",
        from_address="addrA",
        to_address="addrC",
        amount=1.0,
        amount_usd=3500.0,
        token="BTC",
        timestamp=pytest.importorskip("datetime").datetime.now(pytest.importorskip("datetime").timezone.utc),
        chain="bitcoin",
        co_inputs=["addrA", "addrB"],
    )
    apply_cospend_heuristic([tx], ds)
    assert ds.find("addrA") == ds.find("addrB")


def test_peeling_chain_detection(sample_transactions):
    peeling = detect_peeling_chains(sample_transactions)
    assert len(peeling) > 0
    first = peeling[0]
    assert "source" in first
    assert "peel_destination" in first
    assert "change_destination" in first
    assert first["peel_amount_usd"] <= first["change_amount_usd"]


def test_cluster_wallet_network(sample_wallet, sample_transactions):
    clusters = cluster_wallet_network(sample_wallet, sample_transactions)
    assert len(clusters) > 0
    # Root address must be in one of the clusters
    found_root = False
    for c in clusters.values():
        if sample_wallet in c.addresses:
            found_root = True
            break
    assert found_root


# ── Test 4: Graph Construction & Cytoscape Export ─────────────────────────────

def test_build_transaction_graph(sample_wallet, sample_transactions):
    G, clusters = build_transaction_graph(sample_wallet, sample_transactions)
    assert G.number_of_nodes() > 0
    assert G.number_of_edges() > 0
    assert sample_wallet in G.nodes

    cyto = export_cytoscape_json(G, clusters, sample_wallet)
    assert "elements" in cyto
    assert "nodes" in cyto["elements"]
    assert "edges" in cyto["elements"]
    assert "summary" in cyto
    assert cyto["summary"]["total_volume_usd"] > 0


# ── Test 5: GraphSAGE GNN Inference ───────────────────────────────────────────

def test_gnn_feature_extraction(sample_wallet, sample_transactions):
    G, _ = build_transaction_graph(sample_wallet, sample_transactions)
    node_ids, feats, adj = extract_node_features_16dim(G, sample_wallet, set())
    assert len(node_ids) == G.number_of_nodes()
    assert len(feats) == len(node_ids)
    assert len(feats[0]) == 16  # 16-dim Elliptic features
    assert len(adj) == len(node_ids)


def test_gnn_classification(sample_wallet, sample_transactions):
    G, _ = build_transaction_graph(sample_wallet, sample_transactions)
    res = gnn_service.classify_graph(G, sample_wallet)
    assert "root_category" in res
    assert res["root_category"] in ["exchange", "mixer", "mule", "unknown"]
    assert "confidence" in res
    assert "attributed_vasp" in res
    assert "node_predictions" in res


# ── Test 6: Withdrawal Prediction ─────────────────────────────────────────────

def test_withdrawal_prediction_features(sample_transactions):
    feat = extract_withdrawal_features(sample_transactions)
    assert feat.inflow_amount_usd > 0
    assert feat.wallet_age_days >= 1.0
    assert 0 <= feat.historical_peak_hour <= 23

    res = withdrawal_predictor.predict(feat, attributed_vasp="Binance")
    assert "UTC" in res.predicted_window_utc
    assert res.confidence > 0.0
    assert res.freeze_urgency in ["CRITICAL", "HIGH", "MEDIUM"]
    assert "Binance" in res.probable_destinations


# ── Test 7: Synthetic Data Generator ──────────────────────────────────────────

def test_synthetic_actor_flow_generation():
    actor, txs = generate_synthetic_actor_flow(base_volume_usd=100000.0)
    assert actor.archetype in ["investment_fraudster", "darknet_vendor", "ransomware_operator"]
    assert len(txs) >= 4
    assert all(tx.amount_usd > 0 for tx in txs)


# ── Test 8: FastAPI REST Endpoints ────────────────────────────────────────────

def test_endpoint_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "chaineye"


def test_endpoint_attribution(client):
    res = client.get("/attribution/0x71c83638379185a61142b19127765f14f0d6498b")
    assert res.status_code == 200
    data = res.json()
    assert "Binance" in data["entity_name"]
    assert data["is_vasp"] is True


def test_endpoint_predict_withdrawal(client):
    res = client.post(
        "/predict/withdrawal",
        json={
            "inflow_amount_usd": 120000.0,
            "wallet_age_days": 5.0,
            "dormancy_hours": 12.0,
            "complaint_lag_hours": 4.0,
            "attributed_vasp": "FixedFloat",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "predicted_window_utc" in data
    assert data["freeze_urgency"] in ["CRITICAL", "HIGH", "MEDIUM"]


def test_endpoint_trace_wallet_evidence_object(client):
    target = "0x71C83638379185a61142b19127765F14f0D6498B"
    case_id = str(uuid4())
    res = client.post(
        "/trace/wallet",
        json={
            "wallet_address": target,
            "case_id": case_id,
            "depth": 3,
            "chain": "ethereum",
            "officer_id": "OFFICER_999",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert "job_id" in data
    job_id = data["job_id"]

    # Verify EvidenceObject structure
    ev = data["evidence"]
    assert ev["module_id"] == "chaineye"
    assert ev["case_id"] == case_id
    assert ev["verdict_code"] == "CHAINEYE_VASP_ATTRIBUTION"
    assert len(ev["artifacts"]) >= 1
    assert ev["artifacts"][0]["file_type"] == "application/json"
    assert ev["hash_sha256"].startswith("0x")
    assert len(ev["hash_sha256"]) == 66

    # Test GET /trace/{job_id}
    job_res = client.get(f"/trace/{job_id}")
    assert job_res.status_code == 200
    assert job_res.json()["job_id"] == job_id


def test_endpoint_trace_transaction(client):
    res = client.post(
        "/trace/transaction",
        json={
            "tx_hash": "0x456789abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234",
            "chain": "ethereum",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"


def test_endpoint_graph(client):
    target = "0x71C83638379185a61142b19127765F14f0D6498B"
    res = client.get(f"/graph/{target}")
    assert res.status_code == 200
    data = res.json()
    assert "elements" in data
    assert "nodes" in data["elements"]
    assert "edges" in data["elements"]

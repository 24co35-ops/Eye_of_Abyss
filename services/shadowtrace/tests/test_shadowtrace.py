"""ShadowTrace unit and integration tests.

Tests cover:
- Stylometry feature extraction (lexical, syntactic, n-gram, BERT fallback)
- Cosine similarity and fingerprint vector normalization
- In-memory vectorstore and k-NN search
- Temporal analysis: UTC histogram, FFT periodicity, timezone inference
- NetworkX actor correlation graph and exports (Cytoscape JSON, GraphML)
- Synthetic corpus generation and seeding
- API endpoints: /health, /fingerprint, /attribute, /actors/{id}, /actors, /graph/export
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import uuid
import pytest
import numpy as np
from fastapi.testclient import TestClient

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SVC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHARED = os.path.abspath(os.path.join(ROOT, "shared"))

os.environ["SHADOWTRACE_OFFLINE"] = "1"

for p in (ROOT, SVC, SHARED):
    if p not in sys.path:
        sys.path.insert(0, p)

from stylometry.features import (
    FINGERPRINT_DIM,
    bert_embedding,
    cosine_similarity,
    extract_fingerprint,
    fit_tfidf,
    lexical_features,
    ngram_features,
    syntactic_features,
)
from stylometry.vectorstore import (
    get_actor,
    get_all_actors,
    knn_search,
    store_size,
    upsert_actor,
)
from temporal.analysis import (
    build_activity_histogram,
    fft_periodicity,
    infer_timezone,
    temporal_profile,
)
from network.graph import (
    add_actor_edge,
    add_actor_node,
    export_cytoscape_json,
    export_graphml,
    get_actor_neighbors,
    reset_actor_graph,
)
from corpus import (
    get_actor_profile,
    get_all_profiles,
    load_synthetic_corpus,
)
from services.shadowtrace.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


SAMPLE_INVESTMENT_TEXT = (
    "Exclusive VIP investment opportunity! Guaranteed 25% weekly ROI via algorithmic arbitrage bot on DEX. "
    "Direct message @phantom_trade for instant node setup. Limited slots remaining! Act now!"
)

SAMPLE_DARKNET_TEXT = (
    "Top grade stealth shipping worldwide! Vacuum sealed x3 with decoy electronics packaging. "
    "FE discount 10% on orders above 2 BTC. Check PGP key in Dread sub."
)


# ── Stylometry Feature Extraction Tests ───────────────────────────────────────

def test_lexical_features():
    feat = lexical_features(SAMPLE_INVESTMENT_TEXT)
    assert len(feat) == 4
    ttr, avg_len, hapax, yule = feat
    assert 0.0 < ttr <= 1.0
    assert avg_len > 2.0
    assert 0.0 <= hapax <= 1.0
    assert yule >= 0.0


def test_lexical_features_empty():
    feat = lexical_features("")
    assert len(feat) == 4
    assert np.all(feat == 0.0)


def test_syntactic_features():
    feat = syntactic_features(SAMPLE_INVESTMENT_TEXT)
    assert len(feat) == 9
    avg_len, var_len, sub_ratio, count = feat[:4]
    assert count >= 2  # multiple sentences
    assert avg_len > 0.0
    # punctuation checks: !, ?, ., ,, ;
    exclamations = feat[4]
    assert exclamations > 0.0  # text contains '!'


def test_ngram_features():
    fit_tfidf([SAMPLE_INVESTMENT_TEXT, SAMPLE_DARKNET_TEXT])
    vec = ngram_features(SAMPLE_INVESTMENT_TEXT)
    assert len(vec) == 256
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-3 or norm == 0.0


def test_bert_embedding():
    emb = bert_embedding(SAMPLE_INVESTMENT_TEXT)
    assert len(emb) == 384
    norm = np.linalg.norm(emb)
    assert abs(norm - 1.0) < 1e-2


def test_extract_fingerprint():
    fp = extract_fingerprint(SAMPLE_INVESTMENT_TEXT)
    assert len(fp) == FINGERPRINT_DIM
    assert fp.dtype == np.float32
    norm = np.linalg.norm(fp)
    assert abs(norm - 1.0) < 1e-4


def test_cosine_similarity():
    v1 = extract_fingerprint(SAMPLE_INVESTMENT_TEXT)
    v2 = extract_fingerprint(SAMPLE_INVESTMENT_TEXT)
    sim_self = cosine_similarity(v1, v2)
    assert abs(sim_self - 1.0) < 1e-4

    v3 = np.zeros_like(v1)
    v3[0] = 1.0
    v4 = np.zeros_like(v1)
    v4[1] = 1.0
    sim_ortho = cosine_similarity(v3, v4)
    assert abs(sim_ortho) < 1e-4


# ── Vectorstore Tests ─────────────────────────────────────────────────────────

def test_vectorstore_upsert_and_knn():
    v_inv = extract_fingerprint(SAMPLE_INVESTMENT_TEXT)
    v_dark = extract_fingerprint(SAMPLE_DARKNET_TEXT)

    upsert_actor("act_inv_1", "investor_boss", "telegram", v_inv, {"archetype": "investment_fraudster"})
    upsert_actor("act_dark_1", "dark_vendor_9", "dread", v_dark, {"archetype": "darknet_vendor"})

    assert store_size() >= 2
    assert get_actor("act_inv_1") is not None

    # Search with investment-style text
    query = extract_fingerprint("VIP arbitrage high return signals")
    results = knn_search(query, k=2)
    assert len(results) >= 2
    # First match should have high similarity
    assert results[0]["similarity"] > 0.3


# ── Temporal Analysis Tests ───────────────────────────────────────────────────

def test_temporal_histogram():
    # Timestamps at 14:00 UTC (hour 14)
    timestamps = [
        "2026-03-01T14:15:00Z",
        "2026-03-02T14:30:00Z",
        "2026-03-03T14:45:00Z",
        "2026-03-04T15:00:00Z",
    ]
    hist = build_activity_histogram(timestamps)
    assert len(hist) == 24
    assert np.isclose(hist.sum(), 1.0)
    assert hist[14] == 0.75
    assert hist[15] == 0.25


def test_fft_periodicity():
    # 24-hour diurnal pattern (peak at 14, zero elsewhere)
    hist = np.zeros(24, dtype=np.float32)
    hist[14] = 1.0
    res = fft_periodicity(hist)
    assert "dominant_period_hours" in res
    assert "diurnal_strength" in res
    assert res["diurnal_strength"] >= 0.0


def test_infer_timezone():
    # If peak is at 12:00 UTC and assumed local peak is 15:00, offset should be ~+3
    hist = np.zeros(24, dtype=np.float32)
    hist[12] = 1.0
    tz = infer_timezone(hist)
    assert tz == "UTC+3"


def test_temporal_profile():
    timestamps = [
        "2026-03-01T10:00:00Z",
        "2026-03-01T11:00:00Z",
        "2026-03-01T12:00:00Z",
    ]
    prof = temporal_profile(timestamps)
    assert prof["sample_count"] == 3
    assert len(prof["histogram"]) == 24
    assert "timezone_estimate" in prof


# ── Actor Graph Tests ─────────────────────────────────────────────────────────

def test_actor_graph_nodes_and_edges():
    reset_actor_graph()
    add_actor_node("act_1", "actor_alpha", "telegram", "investment_fraudster")
    add_actor_node("act_2", "actor_beta", "dread", "darknet_vendor")
    add_actor_edge("act_1", "act_2", "co_operation", 0.9)

    neighbors = get_actor_neighbors("act_1")
    assert len(neighbors) == 1
    assert neighbors[0]["actor_id"] == "act_2"

    cyto = export_cytoscape_json()
    assert len(cyto["nodes"]) == 2
    assert len(cyto["edges"]) == 1

    graphml = export_graphml()
    assert "<graphml" in graphml
    assert "actor_alpha" in graphml


# ── Corpus Loading Tests ──────────────────────────────────────────────────────

def test_load_synthetic_corpus():
    count = load_synthetic_corpus(15)
    assert count >= 15
    assert store_size() >= 15
    profiles = get_all_profiles()
    assert len(profiles) >= 15
    p0 = profiles[0]
    assert p0.archetype in ("investment_fraudster", "darknet_vendor", "ransomware_operator", "romance_scammer", "mule_recruiter")


# ── API Endpoint Tests ────────────────────────────────────────────────────────

def test_endpoint_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "shadowtrace"
    assert data["fingerprint_dim"] == FINGERPRINT_DIM


def test_endpoint_fingerprint(client: TestClient):
    payload = {
        "text": SAMPLE_INVESTMENT_TEXT,
        "handle": "@test_investor",
        "platform": "telegram",
    }
    resp = client.post("/fingerprint", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "fingerprint_id" in data
    assert data["vector_dim"] == FINGERPRINT_DIM
    assert len(data["vector"]) == FINGERPRINT_DIM
    assert "lexical_features" in data
    assert "syntactic_features" in data


def test_endpoint_fingerprint_empty_text(client: TestClient):
    resp = client.post("/fingerprint", json={"text": "   "})
    assert resp.status_code in (422, 400)


def test_endpoint_attribute(client: TestClient):
    payload = {
        "text": "Top grade stealth shipping worldwide! Vacuum sealed packaging.",
        "case_id": str(uuid.uuid4()),
        "officer_id": "OFFICER_007",
        "timestamps": ["2026-03-01T16:00:00Z", "2026-03-01T17:00:00Z"],
    }
    resp = client.post("/attribute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "confidence" in data
    assert "timezone_estimate" in data
    assert "evidence_object" in data
    ev = data["evidence_object"]
    assert ev["module_id"] == "shadowtrace"
    assert "hash_sha256" in ev
    assert len(ev["hash_sha256"]) == 64


def test_endpoint_actor_crud(client: TestClient):
    new_actor_id = str(uuid.uuid4())
    create_payload = {
        "archetype": "ransomware_operator",
        "handles": ["@cryptolock_root"],
        "platforms": ["tox", "darknet_forum"],
        "timezone": "UTC+3",
        "active_hours": [8, 9, 10, 11, 12, 13],
        "wallet_addresses": ["bc1q99999999999999999999999999999999999999"],
        "text_sample": "All files encrypted. Contact support via TOX within 48h.",
    }
    # Create actor
    post_resp = client.post("/actors", json=create_payload)
    assert post_resp.status_code == 200
    actor_data = post_resp.json()
    created_id = actor_data["actor_id"]
    assert actor_data["archetype"] == "ransomware_operator"

    # Get actor
    get_resp = client.get(f"/actors/{created_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["archetype"] == "ransomware_operator"


def test_endpoint_get_actor_404(client: TestClient):
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/actors/{fake_id}")
    assert resp.status_code == 404


def test_endpoint_graph_export_cytoscape(client: TestClient):
    resp = client.get("/graph/export?format=cytoscape")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert "elements" in data


def test_endpoint_graph_export_graphml(client: TestClient):
    resp = client.get("/graph/export?format=graphml")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")
    assert "<graphml" in resp.text

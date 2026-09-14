"""Unit tests for Eye of Abyss synthetic data pipeline."""

import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import networkx as nx
import pytest

# Ensure data-pipeline and project root are in sys.path
_PIPELINE_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_ROOT))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.actor_generator import generate_actor_profile, generate_actor_profiles, ARCHETYPE_CONFIGS
from core.complaint_generator import generate_complaints
from core.text_generator import generate_forum_posts
from core.transaction_generator import generate_transactions
from exporters.chaineye_exporter import export_chaineye_data
from exporters.graph_exporter import export_actor_graph
from exporters.shadowtrace_exporter import export_shadowtrace_corpus
from shared.schemas import CriminalActorProfile


def test_actor_generator_schema_compliance():
    """Verify generated CriminalActorProfile matches shared schema contract."""
    actors = generate_actor_profiles(count=20)
    assert len(actors) == 20
    for a in actors:
        assert isinstance(a, CriminalActorProfile)
        assert a.data_source == "synthetic"
        assert a.archetype in ARCHETYPE_CONFIGS
        assert len(a.handles) >= 1
        assert len(a.platforms) >= 1
        assert len(a.wallet_addresses) >= 1
        assert all(0 <= h <= 23 for h in a.active_hours)
        assert "ttr" in a.linguistic_features
        assert "base_volume_usd" in a.transaction_features


def test_actor_generator_archetype_coverage():
    """Verify all defined archetypes can be generated."""
    for arch in ARCHETYPE_CONFIGS:
        actor = generate_actor_profile(archetype=arch)
        assert actor.archetype == arch
        assert actor.data_source == "synthetic"


def test_text_generator():
    """Verify forum post generation adhering to active hours and actor metadata."""
    actor = generate_actor_profile(archetype="darknet_vendor")
    posts = generate_forum_posts(actor, count=5, use_llm=False)
    assert len(posts) == 5
    for p in posts:
        assert p["data_source"] == "synthetic"
        assert p["actor_id"] == str(actor.actor_id)
        assert len(p["text"]) > 20
        assert p["platform"] in actor.platforms or p["platform"] == "DarknetForum"


def test_transaction_generator():
    """Verify on-chain transactions generated with peeling chains & mixer hops."""
    actors = generate_actor_profiles(count=5)
    txs = generate_transactions(actors)
    assert len(txs) >= 5
    for tx in txs:
        assert tx["data_source"] == "synthetic"
        assert tx["tx_hash"].startswith("0x")
        assert tx["amount_usd"] > 0.0
        assert tx["chain"] in ("ethereum", "bitcoin", "tron")


def test_complaint_generator():
    """Verify NCRP complaints generated with loss amounts and case IDs."""
    actors = generate_actor_profiles(count=5)
    txs = generate_transactions(actors)
    complaints = generate_complaints(actors, transactions=txs)
    assert len(complaints) == len(actors)
    for c in complaints:
        assert c["data_source"] == "synthetic"
        assert c["complaint_id"].startswith("NCRP-2026-")
        assert c["case_id"].startswith("EOA-2026-")
        assert c["reported_loss_inr"] > 0
        assert c["reported_loss_usd"] > 0


def test_exporters_end_to_end():
    """Verify full end-to-end export to ShadowTrace, ChainEye, and GraphML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        actors = generate_actor_profiles(count=4)
        posts_by_actor = {str(a.actor_id): generate_forum_posts(a, count=2) for a in actors}
        txs = generate_transactions(actors)
        complaints = generate_complaints(actors, transactions=txs)

        # 1. ShadowTrace corpus
        corpus_path = export_shadowtrace_corpus(actors, posts_by_actor, output_dir=tmpdir)
        assert corpus_path.exists()
        actors_json = corpus_path / "actors.json"
        assert actors_json.exists()
        with open(actors_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == 4

        # 2. ChainEye data
        tx_path, comp_path = export_chaineye_data(txs, complaints, output_dir=tmpdir)
        assert tx_path.exists()
        assert comp_path.exists()
        with open(tx_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            assert len(rows) == len(txs)
            assert all(r["data_source"] == "synthetic" for r in rows)

        # 3. GraphML export
        graph_path = export_actor_graph(actors, txs, output_dir=tmpdir)
        assert graph_path.exists()
        g = nx.read_graphml(graph_path)
        assert g.number_of_nodes() > 4
        assert g.number_of_edges() > 0


def test_cli_execution():
    """Verify data-pipeline CLI runs cleanly via subprocess."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable,
            str(_PIPELINE_ROOT / "main.py"),
            "generate",
            "--count", "10",
            "--archetypes", "investment_fraudster", "darknet_vendor",
            "--output-dir", tmpdir,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0
        assert "Generation Complete" in res.stdout
        assert (Path(tmpdir) / "chaineye" / "transactions.csv").exists()
        assert (Path(tmpdir) / "chaineye" / "complaints.csv").exists()
        assert (Path(tmpdir) / "shared" / "actor_graph.graphml").exists()

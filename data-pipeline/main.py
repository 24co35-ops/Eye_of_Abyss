"""Eye of Abyss — Synthetic training data generator CLI.

Design-doc §5 & README:
  Generates synthetic criminal actor profiles with cross-domain signals across:
  - ShadowTrace corpus (actor posts, stylometry)
  - ChainEye on-chain multi-hop transactions & NCRP complaints
  - Unified NetworkX GraphML actor network graph
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.actor_generator import generate_actor_profiles
from core.complaint_generator import generate_complaints
from core.text_generator import generate_forum_posts
from core.transaction_generator import generate_transactions
from exporters.chaineye_exporter import export_chaineye_data
from exporters.graph_exporter import export_actor_graph
from exporters.shadowtrace_exporter import export_shadowtrace_corpus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("data-pipeline")


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate synthetic criminal actor profiles and export training data."""
    t0 = time.time()
    count: int = args.count
    archetypes: List[str] = args.archetypes
    output_dir: str = args.output_dir
    posts_per_actor: int = args.posts_per_actor
    use_llm: bool = args.use_llm

    print(f"\n=======================================================")
    print(f"  Eye of Abyss -- Synthetic Training Data Generator")
    print(f"=======================================================")
    print(f"  Count:            {count} actor profiles")
    print(f"  Archetypes:       {', '.join(archetypes)}")
    print(f"  Posts / Actor:    {posts_per_actor}")
    print(f"  Use LLM (Claude): {use_llm}")
    print(f"  Output Directory: {output_dir}")
    print(f"=======================================================\n")

    # 1. Generate CriminalActorProfiles
    logger.info("Generating %d CriminalActorProfile records...", count)
    actors = generate_actor_profiles(count=count, archetypes=archetypes)
    logger.info("Successfully generated %d actor profiles.", len(actors))

    # 2. Generate Forum Posts / Stylometric Texts
    logger.info("Generating forum posts across archetypes...")
    posts_by_actor: Dict[str, List[Dict[str, any]]] = {}
    total_posts = 0
    for actor in actors:
        posts = generate_forum_posts(actor, count=posts_per_actor, use_llm=use_llm)
        posts_by_actor[str(actor.actor_id)] = posts
        total_posts += len(posts)
    logger.info("Generated %d total forum posts.", total_posts)

    # 3. Generate On-Chain Transactions
    logger.info("Generating multi-hop on-chain transactions...")
    transactions = generate_transactions(actors)
    logger.info("Generated %d transactions with VASP & mixer labels.", len(transactions))

    # 4. Generate NCRP Complaints
    logger.info("Generating synthetic NCRP complaint records...")
    complaints = generate_complaints(actors, transactions=transactions)
    logger.info("Generated %d synthetic complaint records.", len(complaints))

    # 5. Export Datasets
    logger.info("Exporting ShadowTrace corpus to %s/shadowtrace/corpus ...", output_dir)
    corpus_path = export_shadowtrace_corpus(actors, posts_by_actor, output_dir=output_dir)

    logger.info("Exporting ChainEye transactions.csv & complaints.csv to %s/chaineye ...", output_dir)
    tx_path, comp_path = export_chaineye_data(transactions, complaints, output_dir=output_dir)

    logger.info("Exporting unified actor graph to %s/shared/actor_graph.graphml ...", output_dir)
    graph_path = export_actor_graph(actors, transactions, output_dir=output_dir)

    elapsed = round(time.time() - t0, 2)
    print(f"\n=======================================================")
    print(f"  Generation Complete in {elapsed}s")
    print(f"=======================================================")
    print(f"  [+] ShadowTrace Corpus:  {corpus_path}")
    print(f"  [+] ChainEye TXs:        {tx_path} ({len(transactions)} rows)")
    print(f"  [+] NCRP Complaints:     {comp_path} ({len(complaints)} rows)")
    print(f"  [+] Unified Actor Graph: {graph_path}")
    print(f"  [+] All data tagged:     data_source: synthetic")
    print(f"=======================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Eye of Abyss synthetic data pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate synthetic actor profiles and corpora")
    gen.add_argument("--count", type=int, default=500, help="Number of actor profiles to generate")
    gen.add_argument(
        "--archetypes",
        nargs="+",
        default=["investment_fraudster", "darknet_vendor", "ransomware_operator"],
        help="Target archetypes",
    )
    gen.add_argument("--output-dir", default="./output", help="Destination output directory")
    gen.add_argument("--posts-per-actor", type=int, default=3, help="Number of posts per actor")
    gen.add_argument("--use-llm", action="store_true", help="Use Anthropic Claude API for forum text generation")

    args = parser.parse_args()
    if args.command == "generate":
        cmd_generate(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""ShadowTrace training corpus exporter."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

from shared.schemas import CriminalActorProfile


def export_shadowtrace_corpus(
    actors: List[CriminalActorProfile],
    posts_by_actor: Dict[str, List[Dict[str, any]]],
    output_dir: str = "./output",
) -> Path:
    """
    Exports ShadowTrace corpus:
      - output/shadowtrace/corpus/actor_{actor_id}/posts.txt
      - output/shadowtrace/corpus/actor_{actor_id}/metadata.json
      - output/shadowtrace/corpus/actors.json
    """
    corpus_dir = Path(output_dir) / "shadowtrace" / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    summary_list = []

    for actor in actors:
        aid = str(actor.actor_id)
        actor_dir = corpus_dir / f"actor_{aid}"
        actor_dir.mkdir(parents=True, exist_ok=True)

        actor_posts = posts_by_actor.get(aid, [])

        # Write posts.txt
        posts_path = actor_dir / "posts.txt"
        with open(posts_path, "w", encoding="utf-8") as f:
            for p in actor_posts:
                f.write(f"[{p.get('timestamp')}] [{p.get('platform')}] {p.get('handle')}:\n")
                f.write(f"{p.get('text')}\n\n")

        # Write metadata.json
        meta_dict = actor.model_dump(mode="json")
        meta_dict["post_count"] = len(actor_posts)
        meta_dict["data_source"] = "synthetic"

        meta_path = actor_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        summary_list.append({
            "actor_id": aid,
            "archetype": actor.archetype,
            "handles": actor.handles,
            "platforms": actor.platforms,
            "timezone": actor.timezone,
            "post_count": len(actor_posts),
            "data_source": "synthetic",
        })

    # Master index
    index_path = corpus_dir / "actors.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(summary_list, f, indent=2)

    return corpus_dir

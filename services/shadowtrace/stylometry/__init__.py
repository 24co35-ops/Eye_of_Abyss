"""ShadowTrace — Stylometry subpackage."""

from .features import (
    FINGERPRINT_DIM,
    bert_embedding,
    cosine_similarity,
    extract_fingerprint,
    fit_tfidf,
    lexical_features,
    ngram_features,
    syntactic_features,
)
from .vectorstore import (
    ActorRecord,
    get_actor,
    get_all_actors,
    knn_search,
    store_size,
    upsert_actor,
)

__all__ = [
    "FINGERPRINT_DIM",
    "ActorRecord",
    "bert_embedding",
    "cosine_similarity",
    "extract_fingerprint",
    "fit_tfidf",
    "get_actor",
    "get_all_actors",
    "knn_search",
    "lexical_features",
    "ngram_features",
    "store_size",
    "syntactic_features",
    "upsert_actor",
]

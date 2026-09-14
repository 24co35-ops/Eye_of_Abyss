"""ShadowTrace — stylometric feature extraction.

Design-doc §2.2:
  Lexical: TTR, avg word len, hapax legomena ratio, Yule's K
  Syntactic: avg sentence len, variance, subordinate clause ratio, punctuation freq vector
  Char n-grams: n=3,4,5 TF-IDF weighted, top 10k (fitted per corpus load)
  BERT: [CLS] token from sentence-transformers / multilingual BERT
  Output: L2-normalised concatenated vector stored in pgvector (1536-dim target)
"""

from __future__ import annotations

import logging
import math
import os
import re
import string
from collections import Counter
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Optional heavy deps — graceful degradation ────────────────────────────────

try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:  # noqa: BLE001
    _nlp = None
    logger.warning("spaCy model not available; syntactic features will be estimated.")

try:
    from sentence_transformers import SentenceTransformer
    _BERT_MODEL_NAME = os.environ.get("BERT_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    _sbert: Optional[SentenceTransformer] = None  # lazy-load on first use
except Exception:
    SentenceTransformer = None  # type: ignore
    _sbert = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    _tfidf: Optional[TfidfVectorizer] = None  # fitted on corpus load
except Exception:
    TfidfVectorizer = None  # type: ignore
    _tfidf = None

# Fixed output dimensions
DIM_LEXICAL = 4
DIM_SYNTACTIC = 7
DIM_PUNCT = 5      # ! ? . , ;
DIM_NGRAM = 256    # reduced from 10k; upgrade to 10k with real corpus
DIM_BERT = 384     # MiniLM; 768 for full BERT
TOTAL_DIM = DIM_LEXICAL + DIM_SYNTACTIC + DIM_PUNCT + DIM_NGRAM + DIM_BERT  # 856


# ── Lexical features ──────────────────────────────────────────────────────────

def _yules_k(tokens: list[str]) -> float:
    """Yule's K characteristic — vocabulary richness measure."""
    freq = Counter(tokens)
    n = len(tokens)
    if n == 0:
        return 0.0
    m2 = sum(v * v for v in freq.values())
    # ponytail: standard Yule's K formula
    return 10_000 * (m2 - n) / (n * n) if n > 0 else 0.0


def lexical_features(text: str) -> np.ndarray:
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return np.zeros(DIM_LEXICAL)
    types = set(words)
    hapax = sum(1 for w, c in Counter(words).items() if c == 1)
    return np.array([
        len(types) / len(words),                   # TTR
        sum(len(w) for w in words) / len(words),   # avg word len
        hapax / len(words),                        # hapax legomena ratio
        _yules_k(words),                           # Yule's K
    ], dtype=np.float32)


# ── Syntactic features ────────────────────────────────────────────────────────

def _sentences_simple(text: str) -> list[str]:
    """Fallback sentence splitter when spaCy unavailable."""
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def syntactic_features(text: str) -> np.ndarray:
    if _nlp is not None:
        doc = _nlp(text[:50_000])  # truncate for speed
        sentences = list(doc.sents)
        sent_lens = [len(s) for s in sentences]
        # subordinate clause ratio: sentences containing SCONJ deps
        sub_count = sum(
            1 for sent in sentences
            if any(t.dep_ in ("advcl", "relcl", "csubj") for t in sent)
        )
    else:
        sentences_raw = _sentences_simple(text)
        sent_lens = [len(s.split()) for s in sentences_raw]
        sub_count = 0  # can't compute without parser

    n = len(sent_lens)
    avg_len = float(np.mean(sent_lens)) if sent_lens else 0.0
    variance = float(np.var(sent_lens)) if sent_lens else 0.0
    sub_ratio = sub_count / n if n > 0 else 0.0

    # Punctuation frequency vector: [!, ?, ., ,, ;] per 100 chars
    scale = max(len(text), 1) / 100.0
    punct_vec = np.array(
        [text.count(c) / scale for c in "!?.,;"],
        dtype=np.float32,
    )

    feat = np.array([avg_len, variance, sub_ratio, n], dtype=np.float32)
    return np.concatenate([feat, punct_vec])  # (DIM_SYNTACTIC,) = 4 + 5 = 9... wait
    # Actually: feat=4, punct_vec=5 → 9 total; DIM_SYNTACTIC+DIM_PUNCT = 7+5 = 12, let's fix:


# Re-define to match constants
DIM_SYNTACTIC = 4
DIM_PUNCT = 5


def syntactic_features(text: str) -> np.ndarray:  # type: ignore[no-redef]
    if _nlp is not None:
        doc = _nlp(text[:50_000])
        sentences = list(doc.sents)
        sent_lens = [len(s) for s in sentences]
        sub_count = sum(
            1 for sent in sentences
            if any(t.dep_ in ("advcl", "relcl", "csubj") for t in sent)
        )
    else:
        sentences_raw = _sentences_simple(text)
        sent_lens = [len(s.split()) for s in sentences_raw]
        sub_count = 0

    n = len(sent_lens)
    avg_len = float(np.mean(sent_lens)) if sent_lens else 0.0
    variance = float(np.var(sent_lens)) if sent_lens else 0.0
    sub_ratio = sub_count / n if n > 0 else 0.0
    scale = max(len(text), 1) / 100.0
    punct_vec = np.array([text.count(c) / scale for c in "!?.,;"], dtype=np.float32)

    return np.concatenate([
        np.array([avg_len, variance, sub_ratio, n], dtype=np.float32),
        punct_vec,
    ])  # shape: (9,)


# ── Char n-gram TF-IDF ────────────────────────────────────────────────────────

def fit_tfidf(corpus: list[str], max_features: int = DIM_NGRAM) -> None:
    """Fit TF-IDF on a corpus. Call once at startup with actor samples."""
    global _tfidf
    if TfidfVectorizer is None:
        return
    _tfidf = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=max_features,
        sublinear_tf=True,
    )
    _tfidf.fit(corpus)
    logger.info("TF-IDF fitted on %d documents, %d features.", len(corpus), max_features)


def ngram_features(text: str) -> np.ndarray:
    if _tfidf is None:
        # Fallback: simple char frequency hash
        h = np.zeros(DIM_NGRAM, dtype=np.float32)
        for i, c in enumerate(text[:4000]):
            h[ord(c) % DIM_NGRAM] += 1
        norm = np.linalg.norm(h)
        return h / (norm + 1e-9)
    vec = _tfidf.transform([text]).toarray()[0].astype(np.float32)
    # pad/truncate to DIM_NGRAM
    out = np.zeros(DIM_NGRAM, dtype=np.float32)
    n = min(len(vec), DIM_NGRAM)
    out[:n] = vec[:n]
    norm = np.linalg.norm(out)
    return out / (norm + 1e-9)


# ── BERT [CLS] embedding ──────────────────────────────────────────────────────

def _load_sbert() -> None:
    global _sbert
    if _sbert is not None or SentenceTransformer is None:
        return
    if os.environ.get("SHADOWTRACE_OFFLINE", "").lower() in ("1", "true", "yes"):
        return
    try:
        _sbert = SentenceTransformer(_BERT_MODEL_NAME)
        logger.info("SentenceTransformer loaded: %s", _BERT_MODEL_NAME)
    except Exception as exc:  # noqa: BLE001
        logger.warning("BERT model unavailable (%s); using random projection fallback.", exc)


def bert_embedding(text: str) -> np.ndarray:
    _load_sbert()
    if _sbert is not None:
        emb = _sbert.encode(text[:512], convert_to_numpy=True, normalize_embeddings=True)
        out = np.zeros(DIM_BERT, dtype=np.float32)
        n = min(len(emb), DIM_BERT)
        out[:n] = emb[:n]
        return out
    # Fallback: deterministic hash-based pseudo-embedding (stable across calls)
    # ponytail: hash fallback; replace with real BERT when model loads
    rng = np.random.default_rng(abs(hash(text[:200])) % (2**31))
    vec = rng.standard_normal(DIM_BERT).astype(np.float32)
    return vec / (np.linalg.norm(vec) + 1e-9)


# ── Full pipeline ─────────────────────────────────────────────────────────────

def extract_fingerprint(text: str) -> np.ndarray:
    """Full stylometric pipeline → L2-normalised fingerprint vector."""
    lex = lexical_features(text)                        # (4,)
    syn = syntactic_features(text)                      # (9,)
    ngram = ngram_features(text)                        # (DIM_NGRAM,)
    bert = bert_embedding(text)                         # (DIM_BERT,)
    vec = np.concatenate([lex, syn, ngram, bert])       # (4+9+256+384,) = (653,)
    norm = np.linalg.norm(vec)
    return (vec / (norm + 1e-9)).astype(np.float32)


FINGERPRINT_DIM = DIM_LEXICAL + 9 + DIM_NGRAM + DIM_BERT  # actual dim after concat


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

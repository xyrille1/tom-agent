"""Heuristic novelty check: flags generated narratives that read too close to
a known classic false-belief vignette (trigram Jaccard overlap).

This is explicitly a heuristic, not a guarantee (see PRD §15 risks) -- it
exists to catch gross overlap (e.g. a template bug that regenerates the
textbook Sally-Anne paragraph), not to prove semantic novelty.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "reference_corpus" / "classic_vignettes.json"

DEFAULT_THRESHOLD = 0.15


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def trigram_jaccard(text_a: str, text_b: str) -> float:
    a = _ngrams(_tokenize(text_a), 3)
    b = _ngrams(_tokenize(text_b), 3)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_reference_corpus(path: Path = DEFAULT_CORPUS_PATH) -> list[str]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["vignettes"]


def novelty_check(
    narrative_text: str, reference_corpus: list[str], threshold: float = DEFAULT_THRESHOLD
) -> tuple[bool, float, str | None]:
    """Returns (is_novel, max_overlap_score, closest_reference_text_or_None)."""
    best_score = 0.0
    best_ref: str | None = None
    for ref in reference_corpus:
        score = trigram_jaccard(narrative_text, ref)
        if score > best_score:
            best_score = score
            best_ref = ref
    return best_score < threshold, best_score, best_ref

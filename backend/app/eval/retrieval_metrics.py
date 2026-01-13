"""Offline retrieval metrics for RAG evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RelevanceLabel:
    chunk_id: str
    grade: int = 1


def _normalize_labels(labels: Iterable[Mapping]) -> dict[str, int]:
    out: dict[str, int] = {}
    for raw in labels:
        if not isinstance(raw, Mapping):
            continue
        chunk_id = raw.get("chunk_id")
        if not chunk_id:
            continue
        grade = raw.get("grade", 1)
        try:
            grade_int = int(grade)
        except Exception:
            grade_int = 1
        out[str(chunk_id)] = max(out.get(str(chunk_id), 0), grade_int)
    return out


def _top_k(ids: Sequence[str], k: int) -> list[str]:
    if k <= 0:
        return []
    return list(ids[:k])


def recall_at_k(
    retrieved_ids: Sequence[str],
    labels: Iterable[Mapping],
    k: int,
    *,
    min_grade: int = 1,
) -> float:
    label_map = _normalize_labels(labels)
    if not label_map:
        return 0.0
    relevant = {cid for cid, g in label_map.items() if g >= min_grade}
    if not relevant:
        return 0.0
    top = set(_top_k(retrieved_ids, k))
    return 1.0 if relevant.intersection(top) else 0.0


def precision_at_k(
    retrieved_ids: Sequence[str],
    labels: Iterable[Mapping],
    k: int,
    *,
    min_grade: int = 1,
) -> float:
    if k <= 0:
        return 0.0
    label_map = _normalize_labels(labels)
    relevant = {cid for cid, g in label_map.items() if g >= min_grade}
    if not relevant:
        return 0.0
    top = _top_k(retrieved_ids, k)
    if not top:
        return 0.0
    hits = sum(1 for cid in top if cid in relevant)
    return float(hits) / float(len(top))


def mrr_at_k(
    retrieved_ids: Sequence[str],
    labels: Iterable[Mapping],
    k: int,
    *,
    min_grade: int = 1,
) -> float:
    label_map = _normalize_labels(labels)
    relevant = {cid for cid, g in label_map.items() if g >= min_grade}
    if not relevant:
        return 0.0
    top = _top_k(retrieved_ids, k)
    for idx, cid in enumerate(top, start=1):
        if cid in relevant:
            return 1.0 / float(idx)
    return 0.0


def ndcg_at_k(
    retrieved_ids: Sequence[str],
    labels: Iterable[Mapping],
    k: int,
    *,
    use_exp_gain: bool = True,
) -> float:
    """
    Normalized discounted cumulative gain at k.

    If labels are binary, this reduces to the binary nDCG variant.
    """
    label_map = _normalize_labels(labels)
    if not label_map or k <= 0:
        return 0.0

    def gain(rel: int) -> float:
        if rel <= 0:
            return 0.0
        return float((2**rel - 1) if use_exp_gain else rel)

    top = _top_k(retrieved_ids, k)
    dcg = 0.0
    for i, cid in enumerate(top, start=1):
        rel = int(label_map.get(cid, 0))
        if rel <= 0:
            continue
        dcg += gain(rel) / _log2(i + 1)

    ideal_rels = sorted(label_map.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels, start=1):
        if rel <= 0:
            continue
        idcg += gain(int(rel)) / _log2(i + 1)

    if idcg <= 0.0:
        return 0.0
    return dcg / idcg


def coverage(retrieved_ids: Sequence[str]) -> float:
    return 1.0 if retrieved_ids else 0.0


def _log2(x: float) -> float:
    # Avoid importing math in hot paths; this is small and deterministic.
    import math

    return math.log(x, 2)


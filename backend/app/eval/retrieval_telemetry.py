"""Online retrieval telemetry (append-only JSONL logging + best-effort explicit-ref auto-eval)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.eval import retrieval_metrics

settings = get_settings()

_QURAN_RANGE_RE = re.compile(r"\b(\d{1,3})\s*:\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?\b")
_HADITH_NUM_RE = re.compile(r"\b(?:hadith|hadis)\s*#?\s*(\d{1,6})\b", re.IGNORECASE)


def _normalize_dashes(text_value: str) -> str:
    return re.sub(r"[‐‑‒–—−﹣－]", "-", text_value)


def _parse_cutoffs(text_value: str) -> List[int]:
    parts = [p.strip() for p in str(text_value).split(",") if p.strip()]
    cutoffs: List[int] = []
    for p in parts:
        try:
            cutoffs.append(int(p))
        except Exception:
            continue
    return sorted({k for k in cutoffs if k > 0})


def _detect_hadith_collection(query: str) -> Optional[str]:
    ql = query.lower()
    # Keep keys aligned with retriever heuristics and metadata.
    if "bukhari" in ql or "البخاري" in ql:
        return "bukhari"
    if "muslim" in ql or "مسلم" in ql:
        return "muslim"
    if "abu dawud" in ql or "abudawud" in ql or "أبو داود" in ql:
        return "abudawud"
    if "tirmidhi" in ql or "ترمذي" in ql:
        return "tirmidhi"
    if "nasai" in ql or "nasa'i" in ql or "النسائي" in ql:
        return "nasai"
    if "ibn majah" in ql or "ابن ماجه" in ql:
        return "ibnmajah"
    return None


async def infer_explicit_reference_labels(db: AsyncSession, query: str) -> Optional[List[dict]]:
    """
    Best-effort automatic ground-truth labels for explicit reference queries.

    Returns labels like: [{"chunk_id": "...", "grade": 3}, ...] or None if not applicable.
    """
    normalized = _normalize_dashes(query)
    m = _QURAN_RANGE_RE.search(normalized)
    if m:
        surah = int(m.group(1))
        start = int(m.group(2))
        end = int(m.group(3)) if m.group(3) else start
        if end < start:
            start, end = end, start
        ayah_strs = [str(n) for n in range(start, end + 1)]
        sql = """
            SELECT id
            FROM knowledge_chunks
            WHERE source_type = 'quran'
              AND chunk_metadata->>'surah_number' = :surah
              AND chunk_metadata->>'ayah_number' = ANY(:ayahs)
            ORDER BY (chunk_metadata->>'ayah_number')::int
        """
        result = await db.execute(text(sql), {"surah": str(surah), "ayahs": ayah_strs})
        ids = [str(r.id) for r in result.fetchall()]
        if not ids:
            return []
        return [{"chunk_id": cid, "grade": 3} for cid in ids]

    num = _HADITH_NUM_RE.search(query)
    collection = _detect_hadith_collection(query)
    if num and collection:
        hadith_number = num.group(1)
        sql = """
            SELECT id
            FROM knowledge_chunks
            WHERE source_type = 'hadith'
              AND lower(chunk_metadata->>'collection') = :collection
              AND chunk_metadata->>'hadith_number' = :hadith_number
            LIMIT 1
        """
        result = await db.execute(
            text(sql),
            {"collection": collection, "hadith_number": str(hadith_number)},
        )
        row = result.first()
        if not row:
            return []
        return [{"chunk_id": str(row.id), "grade": 3}]

    return None


def compute_stage_metrics(
    stage_ids: List[str],
    *,
    labels: Optional[Iterable[Mapping[str, Any]]],
    cutoffs: List[int],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "count": len(stage_ids),
        "coverage": retrieval_metrics.coverage(stage_ids),
    }
    if labels is None:
        return out
    labels_list = list(labels)
    for k in cutoffs:
        out[f"recall@{k}"] = retrieval_metrics.recall_at_k(stage_ids, labels_list, k, min_grade=1)
        out[f"oracle@{k}"] = retrieval_metrics.recall_at_k(stage_ids, labels_list, k, min_grade=2)
        out[f"mrr@{k}"] = retrieval_metrics.mrr_at_k(stage_ids, labels_list, k, min_grade=1)
        out[f"ndcg@{k}"] = retrieval_metrics.ndcg_at_k(stage_ids, labels_list, k)
        out[f"precision@{k}"] = retrieval_metrics.precision_at_k(stage_ids, labels_list, k, min_grade=1)
    return out


def append_jsonl(path_value: str, event: Mapping[str, Any]) -> None:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


async def log_retrieval_telemetry(
    db: AsyncSession,
    *,
    conversation_id: str,
    user_message_id: str,
    assistant_message_id: str,
    language: str,
    query: str,
    retrieval_trace: Mapping[str, Any],
    chunks_used: List[Mapping[str, Any]],
    citations: List[Mapping[str, Any]],
    topics: List[str],
    latency_ms: Optional[float] = None,
) -> None:
    if not settings.rag_enable_retrieval_telemetry:
        return

    now_ms = int(time.time() * 1000)
    cutoffs = _parse_cutoffs(settings.rag_retrieval_eval_cutoffs)

    labels: Optional[List[dict]] = None
    label_source: Optional[str] = None
    if settings.rag_retrieval_auto_eval_explicit_refs:
        inferred = await infer_explicit_reference_labels(db, query)
        if inferred is not None:
            labels = inferred
            label_source = "explicit_ref_inferred"

    def ids_from_trace(key: str) -> List[str]:
        val = retrieval_trace.get(key) or []
        if key == "fused_candidates":
            return [str(x.get("chunk_id")) for x in val if isinstance(x, Mapping) and x.get("chunk_id")]
        return [str(x.get("chunk_id")) for x in val if isinstance(x, Mapping) and x.get("chunk_id")]

    dense_ids = ids_from_trace("dense_candidates")
    sparse_ids = ids_from_trace("sparse_candidates")
    fused_ids = ids_from_trace("fused_candidates")
    final_ids = ids_from_trace("final_top_k")

    event: Dict[str, Any] = {
        "ts_ms": now_ms,
        "conversation_id": conversation_id,
        "user_message_id": user_message_id,
        "assistant_message_id": assistant_message_id,
        "language": language,
        "query": query if settings.rag_retrieval_telemetry_include_query else None,
        "topics": topics,
        "citations_count": len(citations),
        "latency_ms": latency_ms,
        "labels_source": label_source,
        "labels": labels,
        "trace": retrieval_trace,
        "metrics": {
            "dense_candidates": compute_stage_metrics(dense_ids, labels=labels, cutoffs=cutoffs),
            "sparse_candidates": compute_stage_metrics(sparse_ids, labels=labels, cutoffs=cutoffs),
            "fused_candidates": compute_stage_metrics(fused_ids, labels=labels, cutoffs=cutoffs),
            "final_top_k": compute_stage_metrics(final_ids, labels=labels, cutoffs=cutoffs),
        },
        "chunks_used": chunks_used,
    }

    try:
        append_jsonl(settings.rag_retrieval_telemetry_path, event)
    except Exception:
        # Telemetry should never break chat.
        return


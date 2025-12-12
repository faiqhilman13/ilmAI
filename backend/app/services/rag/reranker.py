"""Reranking services for improving retrieval relevance.

Includes:
- Cross-encoder reranker (local, optional dependency)
- LLM judge reranker (OpenAI/Anthropic via existing LLM client)
"""

from __future__ import annotations

import asyncio
import json
import logging
from functools import lru_cache
from typing import List, Optional

from app.config import get_settings
from app.services.llm import get_llm_client
from app.services.rag.retriever import RetrievedChunk

logger = logging.getLogger(__name__)
settings = get_settings()


try:  # Optional heavy deps
    from sentence_transformers import CrossEncoder  # type: ignore
except Exception:  # pragma: no cover
    CrossEncoder = None  # type: ignore


@lru_cache(maxsize=2)
def _load_cross_encoder(model_name: str):
    if CrossEncoder is None:
        raise ImportError("sentence-transformers is not installed")
    logger.info(f"Loading cross-encoder reranker model: {model_name}")
    return CrossEncoder(model_name)


class CrossEncoderReranker:
    """Rerank retrieved chunks using a cross-encoder model."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.rag_cross_encoder_model
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = _load_cross_encoder(self.model_name)
        return self._model

    async def rerank(
        self, query: str, chunks: List[RetrievedChunk], top_k: int
    ) -> List[RetrievedChunk]:
        if not chunks:
            return []
        try:
            model = self._get_model()
        except Exception as e:
            logger.warning(f"Cross-encoder reranker unavailable: {e}")
            return chunks[:top_k]

        pairs = [(query, c.text_content[:1500]) for c in chunks]

        def _predict():
            return model.predict(pairs)  # type: ignore

        scores = await asyncio.to_thread(_predict)
        scored = list(zip(chunks, scores))
        scored.sort(key=lambda x: float(x[1]), reverse=True)

        reranked: List[RetrievedChunk] = []
        for chunk, score in scored[:top_k]:
            chunk.score = float(score)
            reranked.append(chunk)
        return reranked


class LLMJudgeReranker:
    """Rerank chunks by asking an LLM to judge relevance."""

    def __init__(self):
        self.llm_client = get_llm_client()

    async def rerank(
        self, query: str, chunks: List[RetrievedChunk], top_k: int
    ) -> List[RetrievedChunk]:
        if not chunks:
            return []

        candidates = chunks[: settings.rag_llm_judge_candidates]

        items = []
        for i, c in enumerate(candidates, 1):
            snippet = c.text_content.replace("\n", " ")[:400]
            items.append(f"[{i}] source={c.source_type} text={snippet}")

        system_prompt = (
            "You are a strict relevance judge for retrieval. "
            "Rank candidates by how well they answer the query. "
            "Return ONLY valid JSON."
        )
        user_prompt = f"""
Query:
{query}

Candidates:
{chr(10).join(items)}

Return JSON:
{{
  "ranking": [2, 1, 3]
}}

Rules:
- "ranking" must list candidate numbers in best-to-worst order.
- Use only the candidate text to judge relevance.
"""

        try:
            raw = await self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=200,
            )
            ranking = self._parse_ranking(raw, len(candidates))
        except Exception as e:
            logger.warning(f"LLM judge rerank failed: {e}")
            ranking = []

        if not ranking:
            return candidates[:top_k]

        reranked: List[RetrievedChunk] = []
        used = set()
        for idx in ranking:
            if 1 <= idx <= len(candidates):
                c = candidates[idx - 1]
                if c.id not in used:
                    reranked.append(c)
                    used.add(c.id)
            if len(reranked) >= top_k:
                break

        # Fill with leftovers in original order
        for c in candidates:
            if len(reranked) >= top_k:
                break
            if c.id not in used:
                reranked.append(c)
                used.add(c.id)

        return reranked

    def _parse_ranking(self, raw: str, max_len: int) -> List[int]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
        try:
            parsed = json.loads(text)
        except Exception:
            return []
        ranking = parsed.get("ranking") if isinstance(parsed, dict) else None
        if not isinstance(ranking, list):
            return []
        out: List[int] = []
        for v in ranking:
            try:
                i = int(v)
            except Exception:
                continue
            if 1 <= i <= max_len and i not in out:
                out.append(i)
        return out


"""Knowledge retrieval service using pgvector + hybrid sparse search."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk
from app.services.llm import get_llm_client
from app.config import get_settings
from app.services.rag.logging_utils import format_box

logger = logging.getLogger(__name__)
settings = get_settings()


class RetrievedChunk:
    """Retrieved knowledge chunk with similarity score."""

    def __init__(
        self,
        id: UUID,
        source_type: str,
        text_content: str,
        text_arabic: Optional[str],
        text_translation: Optional[str],
        metadata: dict,
        score: float,
    ):
        self.id = id
        self.source_type = source_type
        self.text_content = text_content
        self.text_arabic = text_arabic
        self.text_translation = text_translation
        self.metadata = metadata
        self.score = score

    def __repr__(self):
        return f"RetrievedChunk(source_type={self.source_type}, score={self.score:.3f})"


class KnowledgeRetriever:
    """Retrieves relevant knowledge chunks using hybrid dense+sparse search."""

    @dataclass
    class _Candidate:
        chunk: RetrievedChunk
        fused_score: float = 0.0
        dense_score: float = 0.0
        sparse_score: float = 0.0

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_client = get_llm_client()

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        source_filter: Optional[List[str]] = None,
        score_threshold: float = 0.3,
        extra_filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        planned_queries, planned_filters, planned_sources = await self._plan_search(query)
        effective_filters = {**(extra_filters or {}), **planned_filters}
        # Only apply explicit source filters from caller; LLM-planned sources are treated as soft priors.
        effective_source_filter = source_filter
        hard_filters = self._extract_hard_filters(effective_filters, query)

        if logger.isEnabledFor(logging.DEBUG):
            soft_filters = {
                k: v
                for k, v in effective_filters.items()
                if k not in hard_filters and v is not None
            }
            logger.debug(
                format_box(
                    "RETRIEVAL PLAN",
                    [
                        f"original_query: {query}",
                        f"planned_queries({len(planned_queries)}): {planned_queries}",
                        f"hard_filters: {hard_filters}",
                        f"soft_filters: {soft_filters}",
                        f"planned_sources: {planned_sources}",
                        f"hybrid: {settings.rag_use_hybrid}, top_k: {top_k}, threshold: {score_threshold}",
                    ],
                    color="blue",
                )
            )

        dense_k = max(top_k, settings.rag_dense_candidates)
        sparse_k = max(top_k, settings.rag_sparse_candidates)
        rrf_k = max(1, settings.rag_rrf_k)

        async def collect_candidates(
            threshold: float, filters: Optional[Dict[str, Any]]
        ) -> tuple[Dict[UUID, KnowledgeRetriever._Candidate], int, int]:
            candidates: Dict[UUID, KnowledgeRetriever._Candidate] = {}
            total_dense = 0
            total_sparse = 0
            for q in planned_queries:
                dense = await self._dense_search(
                    query=q,
                    top_k=dense_k,
                    source_filter=effective_source_filter,
                    score_threshold=threshold,
                    extra_filters=filters,
                )
                total_dense += len(dense)

                sparse: List[RetrievedChunk] = []
                if settings.rag_use_hybrid:
                    sparse = await self._sparse_search(
                        query=q,
                        top_k=sparse_k,
                        source_filter=effective_source_filter,
                        extra_filters=filters,
                    )
                    total_sparse += len(sparse)

                for rank, chunk in enumerate(dense, start=1):
                    cand = candidates.get(chunk.id)
                    if cand is None:
                        cand = KnowledgeRetriever._Candidate(chunk=chunk)
                        candidates[chunk.id] = cand
                    cand.dense_score = max(cand.dense_score, chunk.score)
                    cand.fused_score += 1.0 / (rrf_k + rank)

                for rank, chunk in enumerate(sparse, start=1):
                    cand = candidates.get(chunk.id)
                    if cand is None:
                        cand = KnowledgeRetriever._Candidate(chunk=chunk)
                        candidates[chunk.id] = cand
                    cand.sparse_score = max(cand.sparse_score, chunk.score)
                    cand.fused_score += 1.0 / (rrf_k + rank)

            return candidates, total_dense, total_sparse

        candidates, total_dense, total_sparse = await collect_candidates(
            score_threshold, hard_filters or None
        )
        if hard_filters:
            unfiltered, dense2, sparse2 = await collect_candidates(score_threshold, None)
            total_dense += dense2
            total_sparse += sparse2
            if not candidates and unfiltered:
                logger.info("Hard filters produced no results; merging unfiltered candidates")
            for cid, cand2 in unfiltered.items():
                cand1 = candidates.get(cid)
                if cand1 is None:
                    candidates[cid] = cand2
                else:
                    cand1.fused_score += cand2.fused_score
                    cand1.dense_score = max(cand1.dense_score, cand2.dense_score)
                    cand1.sparse_score = max(cand1.sparse_score, cand2.sparse_score)
        if not candidates and score_threshold > 0:
            logger.info("No results above threshold; retrying with threshold=0")
            candidates, total_dense, total_sparse = await collect_candidates(0.0, None)

        fused = sorted(candidates.values(), key=lambda c: c.fused_score, reverse=True)

        if settings.rag_use_source_priors:
            priors = self._source_prior_weights(query, effective_filters)
            fused = sorted(
                fused,
                key=lambda c: c.fused_score * priors.get(c.chunk.source_type, 1.0),
                reverse=True,
            )

        selected: List[KnowledgeRetriever._Candidate]
        apply_per_source = (
            settings.rag_per_source_k > 0
            and self._is_quran_cue(query, effective_filters)
        )
        if apply_per_source:
            per_k = settings.rag_per_source_k
            allowed_sources = (
                effective_source_filter
                if effective_source_filter
                else ["quran", "hadith", "fiqh", "fatwa"]
            )
            selected = []
            used: set[UUID] = set()
            for st in allowed_sources:
                st_cands = [c for c in fused if c.chunk.source_type == st]
                for c in st_cands[:per_k]:
                    if c.chunk.id not in used:
                        selected.append(c)
                        used.add(c.chunk.id)
            for c in fused:
                if len(selected) >= top_k:
                    break
                if c.chunk.id not in used:
                    selected.append(c)
                    used.add(c.chunk.id)
        else:
            selected = fused[:top_k]

        fused_chunks: List[RetrievedChunk] = []
        for c in selected[:top_k]:
            c.chunk.score = c.fused_score
            fused_chunks.append(c.chunk)

        if settings.rag_quran_context_window > 0 and self._is_quran_cue(query, effective_filters):
            fused_chunks = await self._expand_quran_window(
                fused_chunks, settings.rag_quran_context_window
            )

        mode = "hybrid" if settings.rag_use_hybrid else "dense"
        logger.info(
            f"Retrieved {len(fused_chunks)} chunks for query ({mode}; dense={total_dense}, sparse={total_sparse}, queries={len(planned_queries)})"
        )
        return fused_chunks

    async def _dense_search(
        self,
        query: str,
        top_k: int,
        source_filter: Optional[List[str]],
        score_threshold: float,
        extra_filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        query_embedding = await self.llm_client.generate_embedding(query)
        embedding_literal = self._format_embedding(query_embedding)

        sql = f"""
            SELECT
                id,
                source_type,
                text_content,
                text_arabic,
                text_translation,
                chunk_metadata as metadata,
                1 - (embedding <=> '{embedding_literal}'::vector) as similarity
            FROM knowledge_chunks
            WHERE embedding IS NOT NULL
        """

        params: Dict[str, Any] = {"threshold": score_threshold, "top_k": top_k}

        if source_filter:
            sql += " AND source_type = ANY(:source_types)"
            params["source_types"] = source_filter

        if extra_filters:
            sql, params = self._apply_extra_filters(sql, params, extra_filters)

        sql += f"""
            AND 1 - (embedding <=> '{embedding_literal}'::vector) >= :threshold
            ORDER BY embedding <=> '{embedding_literal}'::vector
            LIMIT :top_k
        """

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()
        return [
            RetrievedChunk(
                id=row.id,
                source_type=row.source_type,
                text_content=row.text_content,
                text_arabic=row.text_arabic,
                text_translation=row.text_translation,
                metadata=row.metadata or {},
                score=float(row.similarity),
            )
            for row in rows
        ]

    async def _sparse_search(
        self,
        query: str,
        top_k: int,
        source_filter: Optional[List[str]],
        extra_filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedChunk]:
        sql = """
            SELECT
                id,
                source_type,
                text_content,
                text_arabic,
                text_translation,
                chunk_metadata as metadata,
                ts_rank_cd(
                    to_tsvector('simple', text_content),
                    plainto_tsquery('simple', :query)
                ) as rank
            FROM knowledge_chunks
            WHERE to_tsvector('simple', text_content) @@ plainto_tsquery('simple', :query)
        """
        params: Dict[str, Any] = {"query": query, "top_k": top_k}

        if source_filter:
            sql += " AND source_type = ANY(:source_types)"
            params["source_types"] = source_filter

        if extra_filters:
            sql, params = self._apply_extra_filters(sql, params, extra_filters)

        sql += """
            ORDER BY rank DESC
            LIMIT :top_k
        """

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()
        return [
            RetrievedChunk(
                id=row.id,
                source_type=row.source_type,
                text_content=row.text_content,
                text_arabic=row.text_arabic,
                text_translation=row.text_translation,
                metadata=row.metadata or {},
                score=float(row.rank),
            )
            for row in rows
        ]

    async def _plan_search(
        self, query: str
    ) -> tuple[List[str], Dict[str, Any], Optional[List[str]]]:
        filters = self._heuristic_filters(query)
        queries: List[str] = [query]
        source_types: Optional[List[str]] = None

        needs_llm = False
        if settings.rag_multi_query and settings.rag_num_rewrites > 0:
            needs_llm = True
        if settings.rag_self_filtering and not filters:
            needs_llm = True

        if needs_llm:
            system_prompt = (
                "You are a search planner for an Islamic knowledge RAG system. "
                "Return ONLY valid JSON."
            )
            user_prompt = f"""
User query:
{query}

Return a JSON object with:
{{
  "rewrites": ["alternate query 1", "alternate query 2"],
  "filters": {{
    "source_types": ["quran","hadith","fiqh","fatwa"],
    "surah_number": 2,
    "ayah_number": 255,
    "collection": "bukhari",
    "hadith_number": "20",
    "topic": "taharah",
    "madhab": "shafii"
  }}
}}

Rules:
- rewrites should be short search queries, in English/Malay/Arabic/transliteration as helpful.
- omit filters you are unsure about.
- if no rewrites, return an empty list.
"""
            try:
                raw = await self.llm_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.0,
                    max_tokens=300,
                )
                planned = self._try_parse_json(raw)
                if planned:
                    llm_rewrites = planned.get("rewrites") or []
                    if isinstance(llm_rewrites, list):
                        for r in llm_rewrites:
                            if isinstance(r, str) and r.strip():
                                queries.append(r.strip())

                    llm_filters = planned.get("filters") or {}
                    if isinstance(llm_filters, dict):
                        for k, v in llm_filters.items():
                            if v is None:
                                continue
                            if k == "source_types" and isinstance(v, list):
                                allowed = {"quran", "hadith", "fiqh", "fatwa"}
                                source_types = [
                                    str(x).lower()
                                    for x in v
                                    if str(x).lower() in allowed
                                ]
                                continue
                            filters.setdefault(k, v)
            except Exception as e:
                logger.warning(f"Search planning failed, falling back to raw query: {e}")

        deduped: List[str] = []
        for q in queries:
            if q not in deduped:
                deduped.append(q)
        if settings.rag_multi_query and settings.rag_num_rewrites > 0:
            deduped = deduped[: 1 + settings.rag_num_rewrites]
        else:
            deduped = deduped[:1]

        return deduped, filters, source_types

    def _extract_hard_filters(self, filters: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Return only high-confidence filters to apply as SQL constraints."""
        hard_keys = {"surah_number", "ayah_number", "collection", "hadith_number"}
        ql = query.lower()
        if "shafii" in ql or "syafii" in ql or "mazhab" in ql or "madhab" in ql:
            hard_keys.add("madhab")
        return {k: v for k, v in filters.items() if k in hard_keys and v is not None}

    def _heuristic_filters(self, query: str) -> Dict[str, Any]:
        filters: Dict[str, Any] = {}
        m = re.search(
            r"\b(\d{1,3})\s*:\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?\b", query
        )
        if m:
            filters["surah_number"] = int(m.group(1))
            filters["ayah_number"] = int(m.group(2))

        collections = {
            "bukhari": ["bukhari", "bukharī", "البخاري"],
            "muslim": ["muslim", "مسلم"],
            "abudawud": ["abu dawud", "abudawud", "أبو داود"],
            "tirmidhi": ["tirmidhi", "ترمذي"],
            "nasai": ["nasai", "nasa'i", "النسائي"],
            "ibnmajah": ["ibn majah", "ابن ماجه"],
        }
        ql = query.lower()
        for key, variants in collections.items():
            if any(v in ql for v in variants):
                filters["collection"] = key
                break

        num = re.search(r"\b(?:hadith|hadis)\s*#?\s*(\d{1,6})\b", ql)
        if num:
            filters["hadith_number"] = num.group(1)
        return filters

    def _source_prior_weights(
        self, query: str, filters: Dict[str, Any]
    ) -> Dict[str, float]:
        """Heuristic priors to nudge sources based on query intent."""
        weights = {"quran": 1.0, "hadith": 1.0, "fiqh": 1.0, "fatwa": 1.0}
        ql = query.lower()

        quran_cues = [
            "quran",
            "al-quran",
            "alquran",
            "surah",
            "surat",
            "ayat",
            "ayah",
            "verse",
            "القرآن",
        ]
        hadith_cues = [
            "hadith",
            "hadis",
            "riwayat",
            "bukhari",
            "muslim",
            "abu dawud",
            "tirmidhi",
            "nasai",
            "ibn majah",
            "حديث",
        ]
        fiqh_cues = [
            "hukum",
            "fiqh",
            "fatwa",
            "mazhab",
            "madhab",
            "rukun",
            "syarat",
            "wajib",
            "haram",
            "halal",
            "sunat",
            "sunnah",
            "makruh",
            "mubah",
        ]

        if filters.get("surah_number") or re.search(r"\b\d{1,3}:\d{1,3}\b", ql) or any(
            cue in ql for cue in quran_cues
        ):
            weights["quran"] *= 1.4

        if filters.get("hadith_number") or filters.get("collection") or any(
            cue in ql for cue in hadith_cues
        ):
            weights["hadith"] *= 1.3

        if any(cue in ql for cue in fiqh_cues):
            weights["fiqh"] *= 1.2
            weights["fatwa"] *= 1.15

        return weights

    def _is_quran_cue(self, query: str, filters: Dict[str, Any]) -> bool:
        ql = query.lower()
        if filters.get("surah_number") or filters.get("ayah_number"):
            return True
        if re.search(r"\b\d{1,3}:\d{1,3}\b", ql):
            return True
        cues = [
            "quran",
            "al-quran",
            "alquran",
            "surah",
            "surat",
            "ayat",
            "ayah",
            "verse",
            "القرآن",
        ]
        return any(c in ql for c in cues)

    def _try_parse_json(self, text_response: str) -> Optional[Dict[str, Any]]:
        text = text_response.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()
        if not (text.startswith("{") and text.endswith("}")):
            return None
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    async def _expand_quran_window(
        self, chunks: List[RetrievedChunk], window: int
    ) -> List[RetrievedChunk]:
        """Append nearby single-ayah Quran chunks for extra context."""
        expanded: List[RetrievedChunk] = []
        seen: set[UUID] = set()
        for chunk in chunks:
            expanded.append(chunk)
            seen.add(chunk.id)
            if chunk.source_type != "quran":
                continue
            meta = chunk.metadata or {}
            surah = meta.get("surah_number")
            ayah = meta.get("ayah_number")
            if not surah or not ayah:
                continue
            neighbor_nums = [
                n
                for n in range(int(ayah) - window, int(ayah) + window + 1)
                if n != int(ayah) and n > 0
            ]
            if not neighbor_nums:
                continue
            neighbors = await self._fetch_quran_ayahs(int(surah), neighbor_nums)
            for nb in neighbors:
                if nb.id not in seen:
                    expanded.append(nb)
                    seen.add(nb.id)
        return expanded

    async def _fetch_quran_ayahs(
        self, surah_number: int, ayah_numbers: List[int]
    ) -> List[RetrievedChunk]:
        ayah_strs = [str(n) for n in ayah_numbers]
        sql = """
            SELECT
                id,
                source_type,
                text_content,
                text_arabic,
                text_translation,
                chunk_metadata as metadata
            FROM knowledge_chunks
            WHERE source_type = 'quran'
              AND chunk_metadata->>'surah_number' = :surah
              AND chunk_metadata->>'ayah_number' = ANY(:ayahs)
            ORDER BY (chunk_metadata->>'ayah_number')::int
        """
        params = {"surah": str(surah_number), "ayahs": ayah_strs}
        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()
        return [
            RetrievedChunk(
                id=row.id,
                source_type=row.source_type,
                text_content=row.text_content,
                text_arabic=row.text_arabic,
                text_translation=row.text_translation,
                metadata=row.metadata or {},
                score=0.0,
            )
            for row in rows
        ]

    def _apply_extra_filters(
        self, sql: str, params: Dict[str, Any], filters: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        if "surah_number" in filters:
            sql += " AND chunk_metadata->>'surah_number' = :surah_number"
            params["surah_number"] = str(filters["surah_number"])
        if "ayah_number" in filters:
            sql += " AND chunk_metadata->>'ayah_number' = :ayah_number"
            params["ayah_number"] = str(filters["ayah_number"])
        if "collection" in filters:
            sql += " AND lower(chunk_metadata->>'collection') = :collection"
            params["collection"] = str(filters["collection"]).lower()
        if "hadith_number" in filters:
            sql += " AND chunk_metadata->>'hadith_number' = :hadith_number"
            params["hadith_number"] = str(filters["hadith_number"])
        if "topic" in filters:
            sql += " AND lower(chunk_metadata->>'topic') LIKE :topic"
            params["topic"] = f"%{str(filters['topic']).lower()}%"
        if "madhab" in filters:
            sql += " AND lower(chunk_metadata->>'madhab') = :madhab"
            params["madhab"] = str(filters["madhab"]).lower()
        return sql, params

    def _format_embedding(self, embedding: List[float]) -> str:
        return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"

    async def retrieve_by_source(
        self, query: str, source_type: str, top_k: int = 5
    ) -> List[RetrievedChunk]:
        return await self.retrieve(query=query, top_k=top_k, source_filter=[source_type])

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[KnowledgeChunk]:
        result = await self.db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()

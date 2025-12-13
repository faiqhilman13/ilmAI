"""Citation extraction and formatting service."""

import json
import re
import logging
from typing import List, Tuple, Union, Optional, Any

from app.services.rag.retriever import RetrievedChunk
from app.schemas.citation import (
    Citation,
    QuranCitation,
    HadithCitation,
    FiqhCitation,
    FatwaCitation,
)

logger = logging.getLogger(__name__)


class CitationManager:
    """Manages citation extraction and formatting from LLM responses."""

    def format_reference_line(self, citations: List[Citation], language: str = "ms") -> str:
        """Create a deterministic reference line from citation metadata.

        This is used to include clean refs (e.g. "Al-Baqarah 2:256") in the answer
        without trusting the model to print them correctly.
        """
        if not citations:
            return ""

        parts: list[str] = []
        for c in citations:
            if isinstance(c, QuranCitation):
                ayah_range = (
                    f"{c.surah_number}:{c.ayah_start}"
                    if c.ayah_end in (None, c.ayah_start)
                    else f"{c.surah_number}:{c.ayah_start}-{c.ayah_end}"
                )
                parts.append(f"Al-Quran: {c.surah_name} {ayah_range}")
                continue
            if isinstance(c, HadithCitation):
                parts.append(f"Hadith: {c.collection} #{c.hadith_number}")
                continue
            if isinstance(c, FatwaCitation):
                label = f"Fatwa: {c.issuing_authority}"
                if c.fatwa_number:
                    label += f" (#{c.fatwa_number})"
                parts.append(label)
                continue
            if isinstance(c, FiqhCitation):
                label = f"Fiqh: {c.madhab}"
                if c.topic:
                    label += f" ({c.topic})"
                parts.append(label)
                continue

        if not parts:
            return ""

        header = "Rujukan" if language == "ms" else "References"
        return f"{header}: " + "; ".join(parts)

    def sanitize_answer_text(self, answer_text: str, citations: List[Citation]) -> str:
        """Remove/normalize hallucinated inline references that contradict citations.

        The UI renders citations separately. We try to prevent the model from
        emitting misleading parenthetical references like "(Al-Quran, Surah
        Unknown 2:?)" even when the citation indices are correct.
        """
        text = (answer_text or "").strip()
        if not text:
            return text

        # Drop parenthetical "Quran" references which are frequently hallucinated.
        text = re.sub(r"\s*\((?:al-)?qur'?a?n[^)]*\)\s*", " ", text, flags=re.IGNORECASE)

        # If the model wrote "Surah Unknown ..." or "Surah Unknown 2:?", remove the unknown label.
        # Prefer replacing with the first Quran citation's canonical reference if available.
        quran_citations = [c for c in citations if isinstance(c, QuranCitation)]
        if quran_citations:
            qc = quran_citations[0]
            ayah_range = (
                f"{qc.surah_number}:{qc.ayah_start}"
                if qc.ayah_end in (None, qc.ayah_start)
                else f"{qc.surah_number}:{qc.ayah_start}-{qc.ayah_end}"
            )
            canonical = f"Surah {qc.surah_name} {ayah_range}"
            text = re.sub(r"Surah\s+Unknown\s+\d+:\?", canonical, text, flags=re.IGNORECASE)
            text = re.sub(r"Surah\s+Unknown\b", f"Surah {qc.surah_name}", text, flags=re.IGNORECASE)

        # Remove leftover unknown/placeholder verse patterns like "2:?" or "?:?"
        text = re.sub(r"\b\d+:\?\b", "", text)
        text = re.sub(r"\b\?:\?\b", "", text)

        # Normalize whitespace.
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text

    def extract_citations(
        self,
        response: str,
        available_chunks: List[RetrievedChunk],
    ) -> Tuple[str, List[Citation]]:
        """Extract citations from LLM response and validate against available chunks.

        Args:
            response: Raw LLM response text
            available_chunks: List of chunks that were provided as context

        Returns:
            Tuple of (response text, list of validated citations)
        """
        # Prefer structured JSON output if present
        structured = self._try_parse_json_response(response)
        if structured is not None:
            answer_text = str(structured.get("answer", "")).strip()
            indices = self._normalize_indices(structured.get("citations"), len(available_chunks))
            citations = self._citations_from_indices(indices, available_chunks)
            # Remove any stray inline markers to avoid double-rendering
            answer_text = re.sub(r"\s*\[\d+\]\s*", " ", answer_text).strip()
            return answer_text, citations

        # Fallback to bracket markers [1], [2], etc.
        citation_pattern = r"\[(\d+)\]"
        found_indices = set(int(m) for m in re.findall(citation_pattern, response))
        indices = self._normalize_indices(list(found_indices), len(available_chunks))
        citations = self._citations_from_indices(indices, available_chunks)
        return response, citations

    def _try_parse_json_response(self, response: str) -> Optional[dict]:
        """Try to parse a JSON-only response. Returns dict if valid, else None."""
        text = response.strip()
        # Strip common code fences
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()
        if not (text.startswith("{") and text.endswith("}")):
            return None
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "answer" in parsed:
                return parsed
        except Exception:
            return None
        return None

    def _normalize_indices(self, raw: Any, max_index: int) -> List[int]:
        """Normalize citation indices into a sorted unique list within range."""
        if raw is None:
            return []
        indices: List[int] = []
        if isinstance(raw, list):
            for v in raw:
                try:
                    indices.append(int(v))
                except Exception:
                    continue
        else:
            try:
                indices = [int(raw)]
            except Exception:
                indices = []
        valid = sorted({i for i in indices if 1 <= i <= max_index})
        for i in sorted(set(indices) - set(valid)):
            logger.warning(f"Citation index {i} out of range (max: {max_index})")
        return valid

    def _citations_from_indices(
        self, indices: List[int], chunks: List[RetrievedChunk]
    ) -> List[Citation]:
        citations: List[Citation] = []
        for idx in indices:
            chunk = chunks[idx - 1]
            citations.append(self._create_citation(chunk, idx))
        return citations

    def _create_citation(
        self,
        chunk: RetrievedChunk,
        index: int,
    ) -> Citation:
        """Create typed citation based on source type.

        Args:
            chunk: Knowledge chunk
            index: Citation index

        Returns:
            Typed citation object
        """
        # Create text snippet (truncate if too long)
        text_snippet = chunk.text_content
        if len(text_snippet) > 300:
            text_snippet = text_snippet[:300] + "..."

        metadata = chunk.metadata

        if chunk.source_type == "quran":
            surah_number = metadata.get("surah_number", 0)
            surah_name = (
                metadata.get("surah_name")
                or metadata.get("surah_name_ms")
                or metadata.get("surah_name_en")
                or "Unknown"
            )
            # Support both single-ayah and grouped chunk metadata shapes
            ayah_number = metadata.get("ayah_number")
            ayah_start = metadata.get("ayah_start") or ayah_number or 0
            ayah_end = metadata.get("ayah_end")
            if ayah_end is None and metadata.get("ayah_start") is not None:
                ayah_end = ayah_start
            return QuranCitation(
                index=index,
                text_snippet=text_snippet,
                surah_number=int(surah_number) if surah_number is not None else 0,
                surah_name=str(surah_name),
                ayah_start=int(ayah_start) if ayah_start is not None else 0,
                ayah_end=int(ayah_end) if ayah_end is not None else None,
                arabic_text=chunk.text_arabic,
                translation=chunk.text_translation or chunk.text_content,
            )

        elif chunk.source_type == "hadith":
            grading = metadata.get("grading", "unknown")
            # Validate grading value
            if grading not in ["sahih", "hasan", "daif", "mawdu"]:
                grading = "sahih"  # Default to sahih if unknown

            return HadithCitation(
                index=index,
                text_snippet=text_snippet,
                collection=metadata.get("collection", "Unknown"),
                hadith_number=str(metadata.get("hadith_number", "?")),
                grading=grading,
                book_name=metadata.get("book_name"),
                narrator_chain=metadata.get("narrator_chain"),
            )

        elif chunk.source_type == "fiqh":
            return FiqhCitation(
                index=index,
                text_snippet=text_snippet,
                madhab=metadata.get("madhab", "shafii"),
                topic=metadata.get("topic", "General"),
                source_book=metadata.get("source_book"),
                scholar=metadata.get("scholar"),
                evidence=metadata.get("evidence"),
            )

        elif chunk.source_type == "fatwa":
            return FatwaCitation(
                index=index,
                text_snippet=text_snippet,
                issuing_authority=metadata.get("issuing_authority", "Unknown"),
                fatwa_number=metadata.get("fatwa_number"),
                date=metadata.get("date"),
                topic=metadata.get("topic", ""),
            )

        # Fallback for unknown source types
        return FiqhCitation(
            index=index,
            text_snippet=text_snippet,
            madhab="unknown",
            topic="General",
        )

    def build_context_with_markers(
        self,
        chunks: List[RetrievedChunk],
    ) -> str:
        """Build context string with numbered citation markers.

        Args:
            chunks: List of knowledge chunks

        Returns:
            Formatted context string
        """
        from app.services.rag.prompts import format_chunk_for_context

        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            context_parts.append(format_chunk_for_context(chunk, idx))

        return "\n\n---\n\n".join(context_parts)

    def validate_citations(
        self,
        citations: List[Citation],
        response: str,
    ) -> List[Citation]:
        """Validate that all citations are actually referenced in the response.

        Args:
            citations: List of citations
            response: Response text

        Returns:
            List of citations that are actually used in the response
        """
        used_indices = set(int(m) for m in re.findall(r'\[(\d+)\]', response))
        return [c for c in citations if c.index in used_indices]

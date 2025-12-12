"""Main RAG pipeline for Islamic Q&A."""

import json
import logging
from typing import List, Optional, AsyncGenerator, TypedDict, Literal
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.llm import get_llm_client
from app.services.rag.retriever import KnowledgeRetriever, RetrievedChunk
from app.services.rag.citation import CitationManager
from app.services.rag.prompts import get_system_prompt, build_user_prompt
from app.services.rag.logging_utils import format_box
from app.services.rag.reranker import CrossEncoderReranker, LLMJudgeReranker
from app.services.safety.classifier import TopicClassifier
from app.services.safety.disclaimers import DisclaimerService
from app.schemas.chat import ChatResponse
from app.schemas.citation import Citation

logger = logging.getLogger(__name__)
settings = get_settings()


class StreamEvent(TypedDict):
    event: Literal["chunk", "meta"]
    data: str


class RAGResult:
    """Result from RAG pipeline."""

    def __init__(
        self,
        answer: str,
        citations: List[Citation],
        disclaimer: Optional[str],
        topics: List[str],
        language: str,
        chunks_used: List[RetrievedChunk],
    ):
        self.answer = answer
        self.citations = citations
        self.disclaimer = disclaimer
        self.topics = topics
        self.language = language
        self.chunks_used = chunks_used


class IslamicRAGPipeline:
    """RAG pipeline for answering Islamic questions with citations."""

    def __init__(self, db: AsyncSession):
        """Initialize RAG pipeline.

        Args:
            db: Database session
        """
        self.db = db
        self.retriever = KnowledgeRetriever(db)
        self.citation_manager = CitationManager()
        self.topic_classifier = TopicClassifier()
        self.disclaimer_service = DisclaimerService()
        self.llm_client = get_llm_client()
        self.cross_reranker = CrossEncoderReranker() if settings.rag_use_cross_encoder_rerank else None
        self.llm_judge_reranker = LLMJudgeReranker() if settings.rag_use_llm_judge_rerank else None

    async def answer(
        self,
        question: str,
        language: str = "ms",
        conversation_history: Optional[List[dict]] = None,
    ) -> RAGResult:
        """Answer an Islamic question using RAG.

        Args:
            question: User's question
            language: Response language ('ms' or 'en')
            conversation_history: Optional previous messages

        Returns:
            RAGResult with answer, citations, and metadata
        """
        logger.info(format_box("USER QUERY", [question], color="cyan"))
        # 1. Classify topic and check sensitivity
        topics = self.topic_classifier.classify(question)
        topic_names = [t.value for t in topics]
        requires_disclaimer, disclaimer_type = self.topic_classifier.check_sensitivity(topics)
        logger.info(
            format_box(
                "TOPIC CLASSIFICATION",
                [
                    f"topics: {topic_names}",
                    f"requires_disclaimer: {requires_disclaimer}",
                    f"disclaimer_type: {disclaimer_type}",
                ],
                color="magenta",
            )
        )

        # 2. Retrieve relevant knowledge chunks
        chunks = await self.retriever.retrieve(
            query=question,
            top_k=settings.rag_top_k,
            score_threshold=settings.rag_score_threshold,
        )
        retrieval_lines: List[str] = [f"retrieved_chunks: {len(chunks)}"]
        for i, chunk in enumerate(chunks[:5], 1):
            preview = chunk.text_content.replace("\n", " ")[:140]
            retrieval_lines.append(
                f"{i}. {chunk.source_type} score={chunk.score:.3f} {preview}..."
            )
        if not chunks:
            retrieval_lines.append("no chunks matched retrieval criteria")
        logger.info(format_box("RETRIEVAL", retrieval_lines, color="yellow"))

        # 2b. Rerank retrieved chunks (cross-encoder then LLM judge)
        rerank_top_k = min(len(chunks), settings.rag_rerank_top_k or len(chunks))
        if self.cross_reranker and rerank_top_k:
            chunks = await self.cross_reranker.rerank(question, chunks, rerank_top_k)
            logger.info(
                format_box(
                    "RERANK (CROSS-ENCODER)",
                    [f"reranked_top_k: {len(chunks)}"]
                    + [
                        f"{i}. {c.source_type} score={c.score:.3f} {c.text_content.replace(chr(10),' ')[:120]}..."
                        for i, c in enumerate(chunks[:5], 1)
                    ],
                    color="yellow",
                )
            )
        else:
            chunks = chunks[:rerank_top_k]

        if self.llm_judge_reranker and rerank_top_k:
            chunks = await self.llm_judge_reranker.rerank(question, chunks, rerank_top_k)
            logger.info(
                format_box(
                    "RERANK (LLM JUDGE)",
                    [f"reranked_top_k: {len(chunks)}"]
                    + [
                        f"{i}. {c.source_type} {c.text_content.replace(chr(10),' ')[:120]}..."
                        for i, c in enumerate(chunks[:5], 1)
                    ],
                    color="yellow",
                )
            )

        # 3. Handle case where no relevant chunks found
        if not chunks:
            no_info_response = self._get_no_info_response(language)
            return RAGResult(
                answer=no_info_response,
                citations=[],
                disclaimer=None,
                topics=topic_names,
                language=language,
                chunks_used=[],
            )

        # 4. Build prompts (structured JSON output)
        system_prompt = get_system_prompt(language, structured=True)
        user_prompt = build_user_prompt(
            question=question,
            chunks=chunks,
            language=language,
            conversation_history=conversation_history,
            structured=True,
        )

        # 5. Generate response from LLM (retry once if citations missing)
        logger.info(format_box("LLM GENERATION", ["calling model with context"], color="blue"))
        raw_response, _ = await self._generate_with_citation_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            chunks=chunks,
        )
        logger.info(format_box("LLM RESPONSE (RAW)", [raw_response], color="green"))

        # 6. Extract and validate citations
        answer_text, citations = self.citation_manager.extract_citations(
            response=raw_response,
            available_chunks=chunks,
        )
        citation_indices = [c.index for c in citations]
        logger.info(
            format_box(
                "FINAL ANSWER",
                [
                    answer_text,
                    f"citations: {citation_indices}",
                ],
                color="green",
            )
        )

        # 7. Add disclaimer if needed
        disclaimer = None
        if requires_disclaimer:
            disclaimer = self.disclaimer_service.get_disclaimer(
                disclaimer_type=disclaimer_type,
                language=language,
            )

        return RAGResult(
            answer=answer_text,
            citations=citations,
            disclaimer=disclaimer,
            topics=topic_names,
            language=language,
            chunks_used=chunks,
        )

    async def answer_stream(
        self,
        question: str,
        language: str = "ms",
        conversation_history: Optional[List[dict]] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream answer to an Islamic question.

        Args:
            question: User's question
            language: Response language
            conversation_history: Optional previous messages

        Yields:
            Text chunks as they are generated
        """
        # 1. Classify and retrieve (same as non-streaming)
        logger.info(format_box("USER QUERY (STREAM)", [question], color="cyan"))
        topics = self.topic_classifier.classify(question)
        topic_names = [t.value for t in topics]
        requires_disclaimer, disclaimer_type = self.topic_classifier.check_sensitivity(topics)
        chunks = await self.retriever.retrieve(
            query=question,
            top_k=settings.rag_top_k,
            score_threshold=settings.rag_score_threshold,
        )

        if not chunks:
            logger.info(format_box("RETRIEVAL", ["retrieved_chunks: 0"], color="yellow"))
            yield {"event": "chunk", "data": self._get_no_info_response(language)}
            return

        retrieval_lines: List[str] = [f"retrieved_chunks: {len(chunks)}"]
        for i, chunk in enumerate(chunks[:5], 1):
            preview = chunk.text_content.replace("\n", " ")[:140]
            retrieval_lines.append(
                f"{i}. {chunk.source_type} score={chunk.score:.3f} {preview}..."
            )
        logger.info(format_box("RETRIEVAL", retrieval_lines, color="yellow"))

        rerank_top_k = min(len(chunks), settings.rag_rerank_top_k or len(chunks))
        if self.cross_reranker and rerank_top_k:
            chunks = await self.cross_reranker.rerank(question, chunks, rerank_top_k)
            logger.info(format_box("RERANK (CROSS-ENCODER)", [f"reranked_top_k: {len(chunks)}"], color="yellow"))
        else:
            chunks = chunks[:rerank_top_k]
        if self.llm_judge_reranker and rerank_top_k:
            chunks = await self.llm_judge_reranker.rerank(question, chunks, rerank_top_k)
            logger.info(format_box("RERANK (LLM JUDGE)", [f"reranked_top_k: {len(chunks)}"], color="yellow"))

        # 2. Build prompts (non-structured for cleaner streaming)
        system_prompt = get_system_prompt(language, structured=False)
        user_prompt = build_user_prompt(
            question=question,
            chunks=chunks,
            language=language,
            conversation_history=conversation_history,
            structured=False,
        )

        # 3. Stream response and accumulate full text
        full_response = ""
        async for chunk in self.llm_client.generate_stream(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=2000,
        ):
            full_response += chunk
            yield {"event": "chunk", "data": chunk}

        # 4. After stream, emit meta with citations/disclaimer/topics
        _, citations = self.citation_manager.extract_citations(
            response=full_response,
            available_chunks=chunks,
        )
        logger.info(format_box("LLM RESPONSE (STREAM RAW)", [full_response], color="green"))
        disclaimer = None
        if requires_disclaimer:
            disclaimer = self.disclaimer_service.get_disclaimer(
                disclaimer_type=disclaimer_type,
                language=language,
            )

        meta = {
            "citations": [c.model_dump() for c in citations],
            "topics": topic_names,
            "language": language,
            "disclaimer": disclaimer,
        }
        yield {"event": "meta", "data": json.dumps(meta, ensure_ascii=False)}

    def _get_no_info_response(self, language: str) -> str:
        """Get response when no relevant information is found.

        Args:
            language: Response language

        Returns:
            Appropriate "no information" message
        """
        if language == "ms":
            return """Maaf, saya tidak menemui maklumat khusus mengenai soalan ini dalam sumber rujukan yang ada.

Sila cuba:
1. Menyoal dengan lebih terperinci
2. Menggunakan istilah yang berbeza
3. Merujuk terus kepada ustaz atau mufti untuk soalan yang kompleks

Adakah terdapat aspek lain yang boleh saya bantu?"""
        else:
            return """I apologize, but I could not find specific information about this question in the available reference sources.

Please try:
1. Asking with more detail
2. Using different terms
3. Consulting directly with a religious scholar for complex questions

Is there another aspect I can help you with?"""

    async def _generate_with_citation_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        chunks: List[RetrievedChunk],
    ) -> tuple[str, List[Citation]]:
        """Generate response and retry once if citations are missing."""
        raw = await self.llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=2000,
        )
        _, citations = self.citation_manager.extract_citations(raw, chunks)
        if citations:
            return raw, citations

        retry_prompt = (
            user_prompt
            + "\n\nIMPORTANT: Return ONLY valid JSON and include non-empty 'citations' indices if any sources were used."
        )
        raw_retry = await self.llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=retry_prompt,
            temperature=0.1,
            max_tokens=2000,
        )
        _, citations_retry = self.citation_manager.extract_citations(raw_retry, chunks)
        return raw_retry, citations_retry

    async def get_suggested_questions(
        self,
        current_question: str,
        language: str = "ms",
    ) -> List[str]:
        """Generate suggested follow-up questions.

        Args:
            current_question: Current question
            language: Language for suggestions

        Returns:
            List of suggested questions
        """
        # For MVP, return static suggestions based on detected topics
        topics = self.topic_classifier.classify(current_question)

        suggestions_ms = {
            "fiqh_ibadah": [
                "Apakah syarat sah solat?",
                "Bagaimana cara mengqada solat yang tertinggal?",
                "Apakah perkara yang membatalkan puasa?",
            ],
            "fiqh_munakahat": [
                "Apakah rukun nikah dalam Islam?",
                "Bagaimana prosedur perceraian dalam Islam?",
            ],
            "hadith": [
                "Apakah maksud hadis sahih?",
                "Bagaimana cara mengetahui hadis itu sahih atau palsu?",
            ],
        }

        suggestions_en = {
            "fiqh_ibadah": [
                "What are the conditions for valid prayer?",
                "How to make up missed prayers?",
                "What things invalidate fasting?",
            ],
            "fiqh_munakahat": [
                "What are the pillars of marriage in Islam?",
                "What is the procedure for divorce in Islam?",
            ],
            "hadith": [
                "What does sahih hadith mean?",
                "How to know if a hadith is authentic or fabricated?",
            ],
        }

        suggestions = suggestions_ms if language == "ms" else suggestions_en

        for topic in topics:
            if topic.value in suggestions:
                return suggestions[topic.value]

        # Default suggestions
        if language == "ms":
            return [
                "Bagaimana cara solat yang betul?",
                "Apakah rukun Islam?",
                "Bagaimana cara berwuduk?",
            ]
        return [
            "What is the correct way to pray?",
            "What are the pillars of Islam?",
            "How to perform ablution (wudu)?",
        ]

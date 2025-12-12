"""Knowledge retrieval service using pgvector."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk
from app.services.llm import get_llm_client
from app.config import get_settings

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
    """Retrieves relevant knowledge chunks using vector similarity search."""

    def __init__(self, db: AsyncSession):
        """Initialize retriever with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.llm_client = get_llm_client()

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        source_filter: Optional[List[str]] = None,
        score_threshold: float = 0.3,
    ) -> List[RetrievedChunk]:
        """Retrieve relevant knowledge chunks for a query.

        Args:
            query: User's question
            top_k: Maximum number of chunks to retrieve
            source_filter: Optional list of source types to filter (e.g., ['quran', 'hadith'])
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of retrieved chunks sorted by relevance
        """
        # Generate embedding for query
        query_embedding = await self.llm_client.generate_embedding(query)
        embedding_literal = self._format_embedding(query_embedding)

        # Build SQL query with vector similarity
        # Using cosine distance (1 - cosine_similarity) so lower is better
        # Convert to similarity score: 1 - distance
        sql = """
            SELECT
                id,
                source_type,
                text_content,
                text_arabic,
                text_translation,
                metadata,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM knowledge_chunks
            WHERE embedding IS NOT NULL
        """

        params = {"embedding": embedding_literal, "top_k": top_k}

        # Add source filter if provided
        if source_filter:
            sql += " AND source_type = ANY(:source_types)"
            params["source_types"] = source_filter

        # Add similarity threshold and ordering
        sql += """
            AND 1 - (embedding <=> :embedding::vector) >= :threshold
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """
        params["threshold"] = score_threshold

        # Execute query
        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        # Convert to RetrievedChunk objects
        chunks = []
        for row in rows:
            chunk = RetrievedChunk(
                id=row.id,
                source_type=row.source_type,
                text_content=row.text_content,
                text_arabic=row.text_arabic,
                text_translation=row.text_translation,
                metadata=row.metadata or {},
                score=float(row.similarity),
            )
            chunks.append(chunk)

        logger.info(f"Retrieved {len(chunks)} chunks for query (top_k={top_k})")
        return chunks

    def _format_embedding(self, embedding: List[float]) -> str:
        """Format embedding list into pgvector literal."""
        # pgvector accepts '[1,2,3]' string literal
        return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"

    async def retrieve_by_source(
        self,
        query: str,
        source_type: str,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Retrieve chunks from a specific source type.

        Args:
            query: User's question
            source_type: Type of source ('quran', 'hadith', 'fiqh', 'fatwa')
            top_k: Maximum number of chunks

        Returns:
            List of retrieved chunks
        """
        return await self.retrieve(
            query=query,
            top_k=top_k,
            source_filter=[source_type],
        )

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[KnowledgeChunk]:
        """Get a specific chunk by ID.

        Args:
            chunk_id: UUID of the chunk

        Returns:
            Knowledge chunk or None if not found
        """
        result = await self.db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()

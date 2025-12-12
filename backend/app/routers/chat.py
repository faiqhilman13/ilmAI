"""Chat router for Islamic Q&A."""

import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.dependencies import Database, CurrentUser, OptionalUser
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.conversation import MessageResponse
from app.models.conversation import Conversation, Message
from app.services.rag.pipeline import IslamicRAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Database,
    current_user: OptionalUser,
):
    """Send a message and get AI response with citations.

    This endpoint:
    1. Creates a new conversation if not provided
    2. Saves user message
    3. Runs RAG pipeline
    4. Saves assistant response with citations
    5. Returns response with citations and disclaimer if needed
    """
    # Initialize RAG pipeline
    pipeline = IslamicRAGPipeline(db)

    # Get or create conversation
    conversation_id = request.conversation_id
    if conversation_id:
        # Verify conversation exists and belongs to user
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        if current_user and conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id if current_user else None,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            language=request.language,
        )
        db.add(conversation)
        await db.flush()
        conversation_id = conversation.id

    # Get conversation history for context
    conversation_history = None
    if conversation_id:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(6)
        )
        messages = result.scalars().all()
        if messages:
            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in reversed(messages)
            ]

    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    await db.flush()

    # Run RAG pipeline
    try:
        result = await pipeline.answer(
            question=request.message,
            language=request.language,
            conversation_history=conversation_history,
        )
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response. Please try again.",
        )

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=result.answer,
        citations=[c.model_dump() for c in result.citations] if result.citations else None,
        disclaimer=result.disclaimer,
        topics=result.topics,
    )
    db.add(assistant_message)
    await db.commit()

    return ChatResponse(
        answer=result.answer,
        citations=result.citations,
        disclaimer=result.disclaimer,
        topics=result.topics,
        language=result.language,
        message_id=assistant_message.id,
        conversation_id=conversation_id,
    )


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    db: Database,
    current_user: OptionalUser,
):
    """Send a message and get streaming AI response.

    Returns a Server-Sent Events stream of the response.
    Note: Citations are returned after the full response is generated.
    """
    pipeline = IslamicRAGPipeline(db)

    async def generate():
        async for event in pipeline.answer_stream(
            question=request.message,
            language=request.language,
        ):
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/suggestions")
async def get_suggested_questions(
    question: str,
    language: str = "ms",
    db: Database = None,
):
    """Get suggested follow-up questions based on the current question."""
    pipeline = IslamicRAGPipeline(db)
    suggestions = await pipeline.get_suggested_questions(question, language)
    return {"suggestions": suggestions}

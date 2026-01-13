"""Chat router for Islamic Q&A."""

import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.dependencies import Database, CurrentUser, OptionalUser
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.conversation import MessageResponse
from app.models.conversation import Conversation, Message
from app.services.rag.pipeline import IslamicRAGPipeline
from app.eval.retrieval_telemetry import log_retrieval_telemetry
from app.core.concurrency import rag_concurrency_limit, get_rag_queue_status
from app.core.rate_limiter import rate_limit_chat
from app.core.job_queue import create_job, get_job, update_job_status, JobStatus, process_job_async
from app.core.circuit_breaker import get_all_circuit_statuses

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse, response_model_by_alias=True)
async def send_message(
    request: ChatRequest,
    http_request: Request,
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
    # Apply rate limiting
    user_id = str(current_user.id) if current_user else None
    await rate_limit_chat(http_request, user_id)

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

    # Run RAG pipeline with concurrency limiting
    try:
        async with rag_concurrency_limit():
            result = await pipeline.answer(
                question=request.message,
                language=request.language,
                conversation_history=conversation_history,
            )
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 503 from concurrency limit)
        raise
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
        citations=[c.model_dump(by_alias=True) for c in result.citations] if result.citations else None,
        disclaimer=result.disclaimer,
        topics=result.topics,
    )
    db.add(assistant_message)
    await db.commit()

    try:
        await log_retrieval_telemetry(
            db,
            conversation_id=str(conversation_id),
            user_message_id=str(user_message.id),
            assistant_message_id=str(assistant_message.id),
            language=request.language,
            query=request.message,
            retrieval_trace=result.retrieval_trace or {},
            chunks_used=[
                {
                    "chunk_id": str(c.id),
                    "source_type": c.source_type,
                    "score": float(c.score),
                }
                for c in (result.chunks_used or [])
            ],
            citations=[c.model_dump(by_alias=True) for c in result.citations] if result.citations else [],
            topics=result.topics or [],
            latency_ms=result.retrieval_latency_ms,
        )
    except Exception:
        # Telemetry should never break chat.
        pass

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
    http_request: Request,
    db: Database,
    current_user: OptionalUser,
):
    """Send a message and get streaming AI response.

    Returns a Server-Sent Events stream of the response.
    Note: Citations are returned after the full response is generated.
    """
    # Apply rate limiting
    user_id = str(current_user.id) if current_user else None
    await rate_limit_chat(http_request, user_id)

    pipeline = IslamicRAGPipeline(db)

    async def generate():
        async with rag_concurrency_limit():
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


@router.get("/status")
async def get_chat_status():
    """Get current chat service status including queue information."""
    return {
        "status": "healthy",
        "queue": get_rag_queue_status(),
        "circuits": get_all_circuit_statuses(),
    }


@router.post("/async")
async def send_message_async(
    request: ChatRequest,
    http_request: Request,
    db: Database,
    current_user: OptionalUser,
):
    """
    Submit a message for async processing.

    Returns a job ID immediately. Use /chat/job/{job_id} to poll for results.
    This endpoint is useful for handling high-traffic scenarios where
    immediate response is not required.
    """
    # Apply rate limiting
    user_id = str(current_user.id) if current_user else None
    await rate_limit_chat(http_request, user_id)

    # Create job
    job_data = {
        "message": request.message,
        "language": request.language,
        "conversation_id": str(request.conversation_id) if request.conversation_id else None,
        "user_id": user_id,
    }

    job_id = await create_job(job_data)

    # Start background processing
    import asyncio

    async def process_chat_job(data: dict) -> dict:
        """Process the chat job."""
        pipeline = IslamicRAGPipeline(db)

        async with rag_concurrency_limit():
            result = await pipeline.answer(
                question=data["message"],
                language=data["language"],
            )

        return {
            "answer": result.answer,
            "citations": [c.model_dump(by_alias=True) for c in result.citations] if result.citations else [],
            "disclaimer": result.disclaimer,
            "topics": result.topics,
            "language": result.language,
        }

    # Schedule background task
    asyncio.create_task(process_job_async(job_id, process_chat_job))

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Request queued for processing. Poll /chat/job/{job_id} for results.",
    }


@router.get("/job/{job_id}")
async def get_job_result(job_id: str):
    """
    Get the result of an async chat job.

    Poll this endpoint until status is 'completed' or 'failed'.
    """
    job = await get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or expired",
        )

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "result": job.result,
        "error": job.error,
    }

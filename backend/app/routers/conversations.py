"""Conversations router."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.dependencies import Database, CurrentUser
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationListItem,
    MessageResponse,
)
from app.models.conversation import Conversation, Message

router = APIRouter()


@router.get("", response_model=List[ConversationListItem])
async def list_conversations(
    db: Database,
    current_user: CurrentUser,
    limit: int = 20,
    offset: int = 0,
):
    """List user's conversations with message counts."""
    # Query conversations with message count
    result = await db.execute(
        select(
            Conversation,
            func.count(Message.id).label("message_count"),
        )
        .outerjoin(Message)
        .where(Conversation.user_id == current_user.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    conversations = []
    for row in result.all():
        conv = row[0]
        count = row[1]
        conversations.append(
            ConversationListItem(
                id=conv.id,
                title=conv.title,
                language=conv.language,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=count,
            )
        )

    return conversations


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    db: Database,
    current_user: CurrentUser,
):
    """Create a new conversation."""
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title,
        language=data.language,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        language=conversation.language,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[],
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: Database,
    current_user: CurrentUser,
):
    """Get a conversation with all messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        language=conversation.language,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                citations=m.citations,
                disclaimer=m.disclaimer,
                topics=m.topics,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    db: Database,
    current_user: CurrentUser,
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conversation)
    await db.commit()


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: UUID,
    title: str,
    db: Database,
    current_user: CurrentUser,
):
    """Update conversation title."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    conversation.title = title
    await db.commit()

    return {"message": "Conversation updated"}

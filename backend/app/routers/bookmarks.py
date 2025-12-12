"""Bookmarks router."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.dependencies import Database, CurrentUser
from app.schemas.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkResponse
from app.schemas.conversation import MessageResponse
from app.models.bookmark import Bookmark
from app.models.conversation import Message

router = APIRouter()


@router.get("", response_model=List[BookmarkResponse])
async def list_bookmarks(
    db: Database,
    current_user: CurrentUser,
    limit: int = 50,
    offset: int = 0,
    tag: str = None,
):
    """List user's bookmarks."""
    query = (
        select(Bookmark)
        .options(joinedload(Bookmark.message))
        .where(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    # Filter by tag if provided
    if tag:
        query = query.where(Bookmark.tags.contains([tag]))

    result = await db.execute(query)
    bookmarks = result.scalars().unique().all()

    return [
        BookmarkResponse(
            id=b.id,
            message_id=b.message_id,
            message=MessageResponse(
                id=b.message.id,
                role=b.message.role,
                content=b.message.content,
                citations=b.message.citations,
                disclaimer=b.message.disclaimer,
                topics=b.message.topics,
                created_at=b.message.created_at,
            ),
            note=b.note,
            tags=b.tags or [],
            created_at=b.created_at,
        )
        for b in bookmarks
    ]


@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    data: BookmarkCreate,
    db: Database,
    current_user: CurrentUser,
):
    """Create a new bookmark."""
    # Check if message exists
    result = await db.execute(select(Message).where(Message.id == data.message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Check if bookmark already exists
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.message_id == data.message_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookmark already exists for this message",
        )

    # Create bookmark
    bookmark = Bookmark(
        user_id=current_user.id,
        message_id=data.message_id,
        note=data.note,
        tags=data.tags,
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)

    return BookmarkResponse(
        id=bookmark.id,
        message_id=bookmark.message_id,
        message=MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            disclaimer=message.disclaimer,
            topics=message.topics,
            created_at=message.created_at,
        ),
        note=bookmark.note,
        tags=bookmark.tags or [],
        created_at=bookmark.created_at,
    )


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: UUID,
    db: Database,
    current_user: CurrentUser,
):
    """Get a specific bookmark."""
    result = await db.execute(
        select(Bookmark)
        .options(joinedload(Bookmark.message))
        .where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == current_user.id,
        )
    )
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    return BookmarkResponse(
        id=bookmark.id,
        message_id=bookmark.message_id,
        message=MessageResponse(
            id=bookmark.message.id,
            role=bookmark.message.role,
            content=bookmark.message.content,
            citations=bookmark.message.citations,
            disclaimer=bookmark.message.disclaimer,
            topics=bookmark.message.topics,
            created_at=bookmark.message.created_at,
        ),
        note=bookmark.note,
        tags=bookmark.tags or [],
        created_at=bookmark.created_at,
    )


@router.patch("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: UUID,
    data: BookmarkUpdate,
    db: Database,
    current_user: CurrentUser,
):
    """Update a bookmark's note or tags."""
    result = await db.execute(
        select(Bookmark)
        .options(joinedload(Bookmark.message))
        .where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == current_user.id,
        )
    )
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    if data.note is not None:
        bookmark.note = data.note
    if data.tags is not None:
        bookmark.tags = data.tags

    await db.commit()
    await db.refresh(bookmark)

    return BookmarkResponse(
        id=bookmark.id,
        message_id=bookmark.message_id,
        message=MessageResponse(
            id=bookmark.message.id,
            role=bookmark.message.role,
            content=bookmark.message.content,
            citations=bookmark.message.citations,
            disclaimer=bookmark.message.disclaimer,
            topics=bookmark.message.topics,
            created_at=bookmark.message.created_at,
        ),
        note=bookmark.note,
        tags=bookmark.tags or [],
        created_at=bookmark.created_at,
    )


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: UUID,
    db: Database,
    current_user: CurrentUser,
):
    """Delete a bookmark."""
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == current_user.id,
        )
    )
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    await db.delete(bookmark)
    await db.commit()


@router.get("/tags/list")
async def list_tags(
    db: Database,
    current_user: CurrentUser,
):
    """Get all unique tags used by the user."""
    result = await db.execute(
        select(Bookmark.tags)
        .where(Bookmark.user_id == current_user.id)
        .where(Bookmark.tags.isnot(None))
    )
    rows = result.all()

    # Flatten and deduplicate tags
    all_tags = set()
    for row in rows:
        if row[0]:
            all_tags.update(row[0])

    return {"tags": sorted(list(all_tags))}

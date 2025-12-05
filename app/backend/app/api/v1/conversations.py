"""Conversation endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from .deps import current_user
from ...db.session import get_db
from ...schemas.conversation import (
    ConversationResponse,
    ConversationCreate,
    ConversationUpdate,
    ConversationDetailResponse,
    MessageResponse
)
from ...models import User
from ...services.history import (
    get_user_conversations,
    create_conversation,
    get_conversation,
    update_conversation,
    delete_conversation,
    get_conversation_messages
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_archived: bool = Query(default=False),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations."""
    conversations = await get_user_conversations(
        db=db,
        user_id=user.id,
        limit=limit,
        offset=offset,
        include_archived=include_archived
    )
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    req: ConversationCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation."""
    conversation = await create_conversation(
        db=db,
        user_id=user.id,
        title=req.title
    )
    return ConversationResponse.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation detail with messages."""
    conversation = await get_conversation(db, conversation_id, user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = await get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset
    )
    
    return ConversationDetailResponse(
        **ConversationResponse.model_validate(conversation).model_dump(),
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation_endpoint(
    conversation_id: UUID,
    req: ConversationUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation (title, archived status)."""
    conversation = await update_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=user.id,
        update_data=req
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation_endpoint(
    conversation_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    deleted = await delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )



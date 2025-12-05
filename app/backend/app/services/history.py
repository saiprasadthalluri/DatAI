"""Conversation and message history service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from ..models import User, Conversation, Message, RouterDecision, MessageRole
from ..schemas.conversation import ConversationCreate, ConversationUpdate


async def get_or_create_user(
    db: AsyncSession,
    firebase_uid: str,
    email: str,
    display_name: Optional[str] = None,
    avatar_url: Optional[str] = None
) -> User:
    """Get or create user from Firebase auth data."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            auth_provider="firebase"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user


async def get_user_conversations(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
    include_archived: bool = False
) -> List[Conversation]:
    """Get user's conversations."""
    query = select(Conversation).where(Conversation.user_id == user_id)
    
    if not include_archived:
        query = query.where(Conversation.archived_at.is_(None))
    
    query = query.order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_conversation(
    db: AsyncSession,
    user_id: UUID,
    title: Optional[str] = None
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=user_id,
        title=title
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID
) -> Optional[Conversation]:
    """Get conversation by ID (with ownership check)."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    update_data: ConversationUpdate
) -> Optional[Conversation]:
    """Update conversation."""
    conversation = await get_conversation(db, conversation_id, user_id)
    if not conversation:
        return None
    
    if update_data.title is not None:
        conversation.title = update_data.title
    
    if update_data.archived is not None:
        if update_data.archived:
            conversation.archived_at = datetime.utcnow()
        else:
            conversation.archived_at = None
    
    conversation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def delete_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID
) -> bool:
    """Delete conversation (cascade deletes messages)."""
    conversation = await get_conversation(db, conversation_id, user_id)
    if not conversation:
        return False
    
    await db.delete(conversation)
    await db.commit()
    return True


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: UUID,
    limit: int = 100,
    offset: int = 0
) -> List[Message]:
    """Get messages for a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def save_message(
    db: AsyncSession,
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    latency_ms: Optional[int] = None,
    safety_labels: Optional[dict] = None
) -> Message:
    """Save a message."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        safety_labels=safety_labels
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def save_router_decision(
    db: AsyncSession,
    message_id: UUID,
    strategy: str,
    selected_endpoint: Optional[str],
    confidence: Optional[float],
    reasons: Optional[dict]
) -> RouterDecision:
    """Save router decision."""
    decision = RouterDecision(
        message_id=message_id,
        strategy=strategy,
        selected_endpoint=selected_endpoint,
        confidence=confidence,
        reasons=reasons
    )
    db.add(decision)
    await db.commit()
    await db.refresh(decision)
    return decision





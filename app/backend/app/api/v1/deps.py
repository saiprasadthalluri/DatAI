"""API dependencies."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from ...core.security import get_current_user
from ...db.session import get_db
from ...services.history import get_or_create_user
from ...models import User


async def current_user(
    firebase_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from database (creates if doesn't exist)."""
    user = await get_or_create_user(
        db=db,
        firebase_uid=firebase_user["uid"],
        email=firebase_user.get("email", ""),
        display_name=firebase_user.get("name"),
        avatar_url=firebase_user.get("picture")
    )
    return user


async def require_admin(
    user: User = Depends(current_user)
) -> User:
    """
    Dependency to require admin access.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(admin: User = Depends(require_admin)):
            ...
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def verify_conversation_owner(
    conversation_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user owns the conversation.
    
    Returns:
        (user, conversation_id) tuple
        
    Raises:
        HTTPException: If conversation doesn't exist or user doesn't own it
    """
    from uuid import UUID
    from ...services.history import get_conversation
    
    try:
        conv_id = UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID"
        )
    
    conversation = await get_conversation(db, conv_id, user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied"
        )
    
    return user, conversation_id

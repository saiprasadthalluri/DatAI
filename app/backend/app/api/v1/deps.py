"""API dependencies."""
import os
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Union
from uuid import UUID, uuid4
from ...core.security import get_current_user
from ...db.session import get_db
from ...services.history import get_or_create_user
from ...services.auth import get_user_by_id
from ...models import User


class MockUser:
    """Mock user for when database is not available."""
    def __init__(self, token_user: dict):
        from datetime import datetime
        self.id = uuid4()
        self.firebase_uid = token_user.get("uid", "dev-user")
        self.email = token_user.get("email", "dev@example.com")
        self.display_name = token_user.get("name", "Dev User")
        self.avatar_url = token_user.get("picture")
        self.is_admin = False
        self.auth_provider = token_user.get("auth_type", "dev")
        self.email_verified = token_user.get("email_verified", False)
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


async def current_user(
    token_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Union[User, MockUser]:
    """Get current user from database (creates if doesn't exist)."""
    try:
        auth_type = token_user.get("auth_type", "")
        
        # For JWT auth, get user directly by ID
        if auth_type == "jwt":
            user = await get_user_by_id(db, token_user["uid"])
            if user:
                return user
        
        # For Firebase or dev auth, use get_or_create
        user = await get_or_create_user(
            db=db,
            firebase_uid=token_user["uid"],
            email=token_user.get("email", ""),
            display_name=token_user.get("name"),
            avatar_url=token_user.get("picture")
        )
        return user
    except Exception as e:
        # If database is not available, return mock user in dev mode
        if os.getenv("ENV") == "development":
            return MockUser(token_user)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not available: {str(e)}"
        )


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

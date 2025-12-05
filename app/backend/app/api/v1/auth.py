"""Auth endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .deps import current_user
from ...db.session import get_db
from ...schemas.auth import UserProfile
from ...models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserProfile)
async def get_me(user: User = Depends(current_user)):
    """Get current user profile."""
    return UserProfile.model_validate(user)


@router.post("/dev-login")
async def dev_login(
    # Only available in development
    # In production, use Firebase Auth SDK on frontend
):
    """Dev login endpoint (placeholder - only in development)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Dev login not implemented. Use Firebase Auth SDK on frontend."
    )



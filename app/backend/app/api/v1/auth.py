"""Auth endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from .deps import current_user
from ...db.session import get_db
from ...schemas.auth import UserProfile
from ...models import User
from ...services.auth import (
    register_user,
    authenticate_user,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


@router.post("/register", response_model=AuthResponse)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with email/password."""
    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    user, error = await register_user(
        db=db,
        email=req.email,
        password=req.password,
        display_name=req.display_name,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    token = create_access_token(str(user.id), user.email)
    
    return AuthResponse(
        access_token=token,
        user=UserProfile.model_validate(user)
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login with email/password."""
    user, error = await authenticate_user(
        db=db,
        email=req.email,
        password=req.password,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )
    
    token = create_access_token(str(user.id), user.email)
    
    return AuthResponse(
        access_token=token,
        user=UserProfile.model_validate(user)
    )


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



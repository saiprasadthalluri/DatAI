"""Security utilities including Firebase token verification."""
import os
from typing import Optional
from fastapi import HTTPException, status, Request
from firebase_admin import credentials, initialize_app, auth
from firebase_admin.exceptions import FirebaseError
import firebase_admin


# Initialize Firebase Admin SDK (lazy initialization)
_firebase_app: Optional[firebase_admin.App] = None


def get_firebase_app():
    """Get or initialize Firebase Admin app."""
    global _firebase_app
    if _firebase_app is None:
        # Use ADC (Application Default Credentials) on Cloud Run
        # For local dev, can use service account JSON via GOOGLE_APPLICATION_CREDENTIALS
        try:
            _firebase_app = initialize_app()
        except ValueError:
            # Already initialized
            _firebase_app = firebase_admin.get_app()
    return _firebase_app


async def verify_firebase_token(token: str) -> dict:
    """
    Verify Firebase ID token and return decoded token.
    
    Args:
        token: Firebase ID token from Authorization header
        
    Returns:
        Decoded token with user info
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Dev mode: accept dev tokens
        env = os.getenv("ENV", "development")
        if env == "development":
            if token.startswith("dev-token-"):
                # Extract user ID from dev token
                uid = token.replace("dev-token-", "")
                return {
                    "uid": uid,
                    "email": "dev@example.com",
                    "email_verified": True,
                    "name": "Dev User"
                }
        
        # Check if using emulator
        emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
        if emulator_host and env == "development":
            # Return mock user for dev emulator
            return {
                "uid": "dev-user-id",
                "email": "dev@example.com",
                "email_verified": True
            }
        
        # Try to verify with Firebase Admin SDK
        try:
            app = get_firebase_app()
            decoded_token = auth.verify_id_token(token, app=app)
            return decoded_token
        except (ValueError, FirebaseError):
            # If Firebase is not configured, allow dev tokens in development
            if env == "development":
                return {
                    "uid": "dev-user-id",
                    "email": "dev@example.com",
                    "email_verified": True
                }
            raise
        
    except Exception as e:
        # In development, be more lenient
        if os.getenv("ENV") == "development":
            return {
                "uid": "dev-user-id",
                "email": "dev@example.com",
                "email_verified": True
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )


async def get_current_user(request: Request) -> dict:
    """
    Dependency to get current user from Firebase token.
    
    Usage:
        @router.get("/me")
        async def get_me(user: dict = Depends(get_current_user)):
            ...
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    token_data = await verify_firebase_token(auth_header)
    return token_data


def setup_cors_middleware(app, allowed_origins: list[str]):
    """Configure CORS middleware with allowed origins."""
    from fastapi.middleware.cors import CORSMiddleware
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_security_headers_middleware(app):
    """Add security headers via middleware."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response
    
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response: Response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            return response
    
    app.add_middleware(SecurityHeadersMiddleware)


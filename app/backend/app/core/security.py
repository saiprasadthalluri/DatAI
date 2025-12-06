"""Security utilities including JWT and Firebase token verification."""
import os
from typing import Optional
from fastapi import HTTPException, status, Request

# Optional Firebase imports (may not be configured)
try:
    from firebase_admin import credentials, initialize_app, auth as firebase_auth
    from firebase_admin.exceptions import FirebaseError
    import firebase_admin
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    firebase_auth = None
    FirebaseError = Exception

from ..services.auth import decode_access_token


# Initialize Firebase Admin SDK (lazy initialization)
_firebase_app = None


def get_firebase_app():
    """Get or initialize Firebase Admin app."""
    global _firebase_app
    if not FIREBASE_AVAILABLE:
        return None
    if _firebase_app is None:
        try:
            _firebase_app = initialize_app()
        except ValueError:
            _firebase_app = firebase_admin.get_app()
        except Exception:
            return None
    return _firebase_app


async def verify_token(token: str) -> dict:
    """
    Verify authentication token (JWT or Firebase).
    
    Args:
        token: Bearer token from Authorization header
        
    Returns:
        Dict with user info (uid, email, etc.)
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    env = os.getenv("ENV", "development")
    
    # 1. Check for dev tokens (development mode only)
    if env == "development" and token.startswith("dev-token-"):
        uid = token.replace("dev-token-", "")
        # Extract email from uid if it looks like an email-based uid
        email = "dev@example.com"
        if uid.startswith("dev-"):
            # Try to reconstruct email from uid
            email_part = uid.replace("dev-", "").replace("-", ".")
            if "@" not in email_part:
                email_part = email_part.replace(".", "@", 1) if "." in email_part else f"{email_part}@example.com"
            email = email_part
        return {
            "uid": uid,
            "email": email,
            "email_verified": True,
            "name": "Dev User",
            "auth_type": "dev"
        }
    
    # 2. Try to decode as our JWT token
    jwt_payload = decode_access_token(token)
    if jwt_payload:
        return {
            "uid": jwt_payload["sub"],
            "email": jwt_payload.get("email", ""),
            "email_verified": True,
            "auth_type": "jwt"
        }
    
    # 3. Try Firebase verification (if available)
    if FIREBASE_AVAILABLE:
        try:
            app = get_firebase_app()
            if app:
                decoded = firebase_auth.verify_id_token(token, app=app)
                return {
                    "uid": decoded["uid"],
                    "email": decoded.get("email", ""),
                    "email_verified": decoded.get("email_verified", False),
                    "name": decoded.get("name"),
                    "picture": decoded.get("picture"),
                    "auth_type": "firebase"
                }
        except Exception:
            pass
    
    # 4. In development, allow any token
    if env == "development":
        return {
            "uid": "dev-user-id",
            "email": "dev@example.com",
            "email_verified": True,
            "auth_type": "dev-fallback"
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token"
    )


# Keep backward compatibility
async def verify_firebase_token(token: str) -> dict:
    """Backward compatible alias for verify_token."""
    return await verify_token(token)


async def get_current_user(request: Request) -> dict:
    """
    Dependency to get current user from token.
    
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
    
    token_data = await verify_token(auth_header)
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


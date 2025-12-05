"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ...db.session import get_db
from ...schemas.common import HealthResponse
from ...core.config import settings
from ...core.rate_limit import get_rate_limiter

router = APIRouter(prefix="/healthz", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    Checks: database, redis, safety (placeholder).
    """
    health = HealthResponse(status="ok")
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health.database = "ok"
    except Exception as e:
        health.database = f"error: {str(e)}"
        health.status = "degraded"
    
    # Check Redis
    try:
        limiter = get_rate_limiter(settings.redis_url)
        client = await limiter._get_client()
        if client:
            await client.ping()
            health.redis = "ok"
        else:
            health.redis = "not available (rate limiting disabled)"
    except Exception as e:
        health.redis = f"error: {str(e)}"
        health.status = "degraded"
    
    # Check Safety (placeholder - always ok since it's a placeholder)
    health.safety = "ok (placeholder)"
    
    return health


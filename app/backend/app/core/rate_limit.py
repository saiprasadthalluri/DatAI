"""Rate limiting using Redis."""
import redis.asyncio as redis
from typing import Optional
from fastapi import HTTPException, status, Request
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client."""
        if self._client is None:
            try:
                self._client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Rate limiting disabled.")
                return None
        return self._client
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier for rate limiting (e.g., user_id or ip)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        try:
            client = await self._get_client()
            if client is None:
                # Redis not available - allow all requests
                return True, limit
            
            # Use sliding window log algorithm
            now = await client.time()
            current_time = now[0] if isinstance(now, tuple) else int(now)
            window_start = current_time - window_seconds
            
            # Remove old entries
            await client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = await client.zcard(key)
            
            if current_count >= limit:
                return False, 0
            
            # Add current request
            await client.zadd(key, {str(current_time): current_time})
            await client.expire(key, window_seconds)
            
            remaining = limit - current_count - 1
            return True, remaining
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True, limit
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(redis_url: str) -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(redis_url)
    return _rate_limiter


async def rate_limit_middleware(
    request: Request,
    user_id: Optional[str] = None,
    per_user_limit: int = 60,
    per_ip_limit: int = 10
):
    """
    Rate limit middleware.
    
    Checks both user-based and IP-based limits.
    """
    from ...core.config import settings
    
    limiter = get_rate_limiter(settings.redis_url)
    
    # Check IP-based limit
    client_ip = request.client.host if request.client else "unknown"
    ip_allowed, ip_remaining = await limiter.check_rate_limit(
        f"rate_limit:ip:{client_ip}",
        per_ip_limit
    )
    
    if not ip_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (IP-based)",
            headers={"X-RateLimit-Remaining": "0"}
        )
    
    # Check user-based limit if authenticated
    if user_id:
        user_allowed, user_remaining = await limiter.check_rate_limit(
            f"rate_limit:user:{user_id}",
            per_user_limit
        )
        
        if not user_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded (user-based)",
                headers={"X-RateLimit-Remaining": "0"}
            )
        
        return user_remaining
    
    return ip_remaining


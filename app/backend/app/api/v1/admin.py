"""Admin endpoints."""
from fastapi import APIRouter, Depends
from .deps import current_user, require_admin
from ...models import User
from ...core.config import settings
from ...core.metrics import get_metrics_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/metrics")
async def get_metrics(user: User = Depends(current_user)):
    """
    Prometheus metrics endpoint.
    
    Returns Prometheus-formatted metrics for monitoring.
    Requires authentication but not admin (for monitoring tools).
    """
    return get_metrics_response()


@router.get("/config")
async def get_config(admin: User = Depends(require_admin)):
    """
    Get current routing configuration (admin only).
    """
    
    return {
        "router_strategy": settings.router_strategy,
        "inference_provider": "OpenRouter",
        "inference_base_url": settings.inference_base_url,
        "models": {
            "theory": settings.model_theory,
            "code": settings.model_code,
            "math": settings.model_math,
            "safety": settings.model_safety,
        },
        "safety_api": "Replicate/LlamaGuard" if settings.safety_api_key != "PLACEHOLDER" else "Not configured",
        "rate_limit_per_user": settings.rate_limit_per_user,
        "rate_limit_per_ip": settings.rate_limit_per_ip,
    }



"""API v1 routes."""
from fastapi import APIRouter
from . import auth, chat, conversations, health, admin, inference

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(conversations.router)
api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(inference.router)





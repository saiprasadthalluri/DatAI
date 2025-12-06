"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .core.logging import setup_logging
from .core.telemetry import setup_telemetry
from .core.security import setup_security_headers_middleware
from .core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .db.init_db import init_db, check_db_connection
from .api.v1 import api_router

# Setup logging
logger = setup_logging(settings.env)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application...")
    
    # Initialize database (non-blocking - allow app to start even if DB fails)
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed (continuing anyway): {e}")
        logger.warning("Backend will start but database features may not work until database is available")
    
    # Check connections (non-blocking)
    try:
        db_ok = await check_db_connection()
        logger.info(f"Database connection: {'OK' if db_ok else 'FAILED'}")
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="ChatApp API",
    description="Dat.AI - Data Science Domain Expert API",
    version="1.0.0",
    lifespan=lifespan
)

# Setup CORS
# Parse comma-separated origins and add common dev ports
allowed_origins = [
    origin.strip() 
    for origin in settings.frontend_origin.split(",")
    if origin.strip()
]
# Always include common development ports
dev_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]
for origin in dev_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup security headers
setup_security_headers_middleware(app)

# Setup telemetry (OpenTelemetry)
setup_telemetry(app, service_name="chatapp-backend")

# Add exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ChatApp API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "development"
    )



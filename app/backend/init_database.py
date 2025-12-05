"""Initialize database using backend's init_db function."""
import asyncio
from app.db.init_db import init_db, check_db_connection
from app.core.logging import setup_logging
from app.core.config import settings

async def main():
    """Initialize database."""
    logger = setup_logging(settings.env)
    logger.info("Testing database connection...")
    
    # Check connection first
    db_ok = await check_db_connection()
    if db_ok:
        logger.info("✅ Database connection successful!")
    else:
        logger.error("❌ Database connection failed!")
        return
    
    # Initialize database (create tables)
    try:
        logger.info("Initializing database tables...")
        await init_db()
        logger.info("✅ Database initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())




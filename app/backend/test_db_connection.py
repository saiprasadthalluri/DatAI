"""Test database connection directly."""
import asyncio
import asyncpg
from app.core.config import settings

async def test_connection():
    """Test direct database connection."""
    try:
        print(f"Attempting to connect to: {settings.database_url}")
        # Extract connection params from URL
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db
        )
        print("✅ Direct connection successful!")
        result = await conn.fetchval("SELECT 1")
        print(f"Query result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())




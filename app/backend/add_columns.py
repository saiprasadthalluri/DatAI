"""Add auth columns to users table."""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    db_url = os.getenv(
        "DATABASE_URL_OVERRIDE",
        "postgresql+asyncpg://chatapp:ChatApp2024Pwd!@/chatapp?host=/cloudsql/chatapp-298b-deploy:us-central1:chatapp-db"
    )
    
    print(f"Connecting to database...")
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        # Add columns if they don't exist
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS firebase_uid VARCHAR(128)"
            ))
            print("Added firebase_uid column")
        except Exception as e:
            print(f"firebase_uid: {e}")
        
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"
            ))
            print("Added password_hash column")
        except Exception as e:
            print(f"password_hash: {e}")
        
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE"
            ))
            print("Added email_verified column")
        except Exception as e:
            print(f"email_verified: {e}")
        
        # Create index on firebase_uid if not exists
        try:
            await conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_firebase_uid ON users(firebase_uid)"
            ))
            print("Created firebase_uid index")
        except Exception as e:
            print(f"firebase_uid index: {e}")
    
    await engine.dispose()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())


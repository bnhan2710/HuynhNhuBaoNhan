# DB connection setup
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

DB_USER = os.getenv("DB_USER", "bnhan2710")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mynameisnhan")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "message-system")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize the database schema."""
    async with engine.begin() as conn:
        # Import models to ensure they are registered
        from .models import User, Message, MessageRecipient  # noqa: F401
        await conn.run_sync(User.__table__.create(bind=conn, checkfirst=True))
        await conn.run_sync(Message.__table__.create(bind=conn, checkfirst=True))
        await conn.run_sync(MessageRecipient.__table__.create(bind=conn, checkfirst=True))

async def test_connection() -> bool:
    """Test the database connection."""
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False
    


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Convert DATABASE_URL to async format for Render compatibility
# Render provides postgres:// or postgresql://, we need postgresql+asyncpg://
def get_async_database_url(url: str) -> str:
    """Convert database URL to async format"""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        return url  # Already in correct format
    else:
        # Assume it needs asyncpg driver
        return f"postgresql+asyncpg://{url.split('://', 1)[-1]}" if "://" in url else url

database_url = get_async_database_url(settings.DATABASE_URL)
logger.info(f"Using database URL scheme: {database_url.split('://')[0]}")

# Create async engine
engine = create_async_engine(
    database_url,
    echo=True,
    poolclass=NullPool,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Alias for background tasks
AsyncSessionLocal = async_session_maker

# Base class for models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database and create tables"""
    try:
        # Import all models to ensure they are registered
        from app.models.user import User
        from app.models.message import Message, Thread
        from app.models.task import Task
        from app.models.instruction import OngoingInstruction
        from app.models.document import Document
        from app.models.webhook_subscription import WebhookSubscription
        
        async with engine.begin() as conn:
            # Enable pgvector extension
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


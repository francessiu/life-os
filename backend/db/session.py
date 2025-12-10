from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

# Note the driver: postgresql+asyncpg (Async) instead of psycopg2 (Sync)
# Ensure DATABASE_URL in .env starts with "postgresql+asyncpg://..."
engine = create_async_engine(settings.DATABASE_URL)

# Create the Async Session factory
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency injection for Routes
async def get_async_session():
    async with async_session_maker() as session:
        yield session
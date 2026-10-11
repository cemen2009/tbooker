import ssl
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from logging import getLogger

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from core.config import get_settings


settings = get_settings()
logger = getLogger(__name__)


def get_ssl_context() -> ssl.SSLContext | None:
    if settings.environment == "dev":
        return None

    try:
        # TODO: add ssl context for production environment in AWS
        ...
    except Exception as e:
        logger.exception(f"Failed to create SSL context: {e}")
        return None


ssl_context = get_ssl_context()
connect_args = {"ssl": ssl_context} if ssl_context else {}

postgres_async_engine: AsyncEngine = create_async_engine(
    settings.db.url,
    echo=True,
    future=True,
    connect_args=connect_args,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)

AsyncPostgresSession: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine=postgres_async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autocommit=False,
)


@asynccontextmanager
async def get_postgres_db_contextmanager() -> AsyncGenerator[AsyncSession]:
    """Yield a PostgreSQL session and close it when the context exits."""
    async with AsyncPostgresSession() as session:
        yield session


async def get_postgres_db() -> AsyncGenerator[AsyncSession]:
    """Yield a PostgreSQL session for dependency-injection consumers."""
    async with get_postgres_db_contextmanager() as session:
        yield session

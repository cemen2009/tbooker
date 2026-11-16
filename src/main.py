import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import get_settings
from core.db.sessions.postgres import postgres_async_engine
from core.logging import setup_logging
from core.redis.registry import RedisRegistry


settings = get_settings()
setup_logging(settings.debug)

logger = logging.getLogger(__name__)
logger.info("Application logger is configured")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    registry = RedisRegistry(settings.redis)
    await registry.start()
    app.state.redis = registry
    try:
        yield
    finally:    # this section under called once application is shut down
        await registry.stop()   # tear down Redis
        await postgres_async_engine.dispose()   # dispose PostgreSQL database


app = FastAPI(
    title="Table Booker",
    debug=settings.debug,
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

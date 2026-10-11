import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import get_settings
from core.db.sessions.postgres import postgres_async_engine
from core.logging import setup_logging

settings = get_settings()
setup_logging(settings.debug)

logger = logging.getLogger(__name__)
logger.info("Application logger is configured")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    try:
        yield
    finally:
        await postgres_async_engine.dispose()


app = FastAPI(title="Table Booker", debug=settings.debug, lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

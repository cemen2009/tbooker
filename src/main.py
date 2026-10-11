import logging

from fastapi import FastAPI

from core.config import get_settings
from core.logging import setup_logging

settings = get_settings()
setup_logging(settings.debug)

logger = logging.getLogger(__name__)
logger.info("Application logger is configured")

app = FastAPI(title="Table Booker", debug=settings.debug)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from fastapi import FastAPI

from core.config import get_settings

settings = get_settings()
# TODO: setup logger

app = FastAPI(title="Table Booker", debug=settings.debug)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

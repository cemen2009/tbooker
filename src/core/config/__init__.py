import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from core.config.settings import Settings

_ENV_FILES = {"dev": ".env.dev", "prod": ".env.prod"}


@lru_cache
def get_settings() -> Settings:

    # reads from the actual process environment — not from any .env file (EXPORT ENVIRONMENT=<prod or dev>)
    env = os.getenv("ENVIRONMENT", "dev")

    env_file = Path(_ENV_FILES.get(env, ".env.dev"))

    if env_file.exists():
        load_dotenv(env_file)
    return Settings(environment=env)  # type: ignore[call-arg]

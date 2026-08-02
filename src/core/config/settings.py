from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DatabaseSettings(BaseSettings):
    host: str
    port: int = 5432
    user: str
    password: str
    name: str

    model_config = SettingsConfigDict(env_prefix="DB_")


class RedisSettings(BaseSettings):
    host: str
    port: int = 6379
    ttl_seconds: int = 30

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class Settings(BaseSettings):
    environment: str = "dev"
    debug: bool = False
    db: DatabaseSettings
    redis: RedisSettings

    model_config = SettingsConfigDict(env_nested_delimiter="__")

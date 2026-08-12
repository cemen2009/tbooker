from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    host: str
    port: int = 5432
    user: str
    password: str
    name: str

    model_config = SettingsConfigDict(env_prefix="DB_")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


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

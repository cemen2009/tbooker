from pydantic import computed_field, SecretStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict()

    host: str
    port: int = 5432
    user: str
    password: str
    name: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisPoolSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        extra="ignore"
    )

    host: str = "redis"
    port: int = 6379
    db: int = 0
    unix_socket_path: str | None = None # overrides host/port

    username: str | None = None
    password: SecretStr | None = None

    # TODO: add other settings + confirm where should TTL live
    # TODO: confirm env_delimiter value to align with main Settings class


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict()

    base: RedisPoolSettings = Field(default_factory=RedisPoolSettings)

    ttl_seconds: int = 30

    # per-role logical DBs
    cache_db: int = 0
    celery_db: int = 1
    ratelimit_db: int = 2
    leaderboard_db: int = 3


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    environment: str = "dev"
    debug: bool = False
    db: DatabaseSettings
    redis: RedisSettings

from typing import Literal

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

    protocol: Literal[2, 3] = 3 # RESP3 needed for push notifications
    decode_responses: bool = False
    encoding: str = "utf-8"
    encoding_errors: Literal["strict", "ignore", "replace"] = "strict"

    socket_connection_timeout: float = 2.0
    socket_timeout: float = 5.0
    pool_wait_timeout: float = 5.0  # BlockingConnectionPool wait

    max_connections: int = 50

    health_check_interval: int = 30
    socket_keepalive: bool = True
    keepalive_idle: int = 60
    keepalive_interval: int = 10
    keepalive_count: int = 3

    retry_attempts: int = 5
    retry_backoff_base: float = .1
    retry_backoff_cap: float = 5.0

    ssl: bool = False
    ssl_cert_reqs: Literal["none", "optional", "required"] = "required"
    ssl_ca_certs: str | None = None
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None
    ssl_check_hostname: bool = True
    ssl_min_version: str | None = None # e.g. "TLSv1_2"

    # identity (shows in CLENT LIST / INFO)
    client_name: str | None = "tbooker"
    lib_name: str | None = "redis-py"
    lib_version: str | None = None

    # maintenance notifications (8.1 async)
    maint_enabled: bool = True
    maint_relaxed_timeout: float = 10.0
    maint_proactive_reconnect: bool = True

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

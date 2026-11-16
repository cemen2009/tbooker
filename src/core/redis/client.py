from __future__ import annotations

import socket
from typing import Any

import redis.asyncio as aioredis
from redis.asynctio.retry import Retry
from redis.backoff import ExponentialWithJitterBackoff
from redis.exceptions import (
    BusyLoadingError,
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)
from redis.maint_notifications import MaintNotificationsConfig # verify in 8.1 docs

from core.config import get_settings
from core.config.settings import RedisPoolSettings


settings = get_settings()
redis_pool_settings = settings.redis_settings.base

def _keep_alive_options() -> dict[int, int]:
    opts: dict[int, int] = {}
    if hasattr(socket, "TCP_KEEPIDLE"):
        opts[socket.TCP_KEEPIDLE] = redis_pool_settings.keepalive_idle
    if hasattr(socket, "TCP_KEEPINTVL"):
        opts[socket.TCP_KEEPINTVL] = redis_pool_settings.keepalive_interval
    if hasattr(socket, "TCP_KEEPCNT"):
        opts[socket.TCP_KEEPCNT] = redis_pool_settings.keepalive_count
    return opts


def build_retry() -> Retry:
    return Retry(
        backoff=ExponentialWithJitterBackoff(
            base=redis_pool_settings.retry_backoff_base,
            cap=redis_pool_settings.retry_backoff_cap
        ),
        retries=redis_pool_settings.retry_attempts,
    )


def build_pool(
        *,
        db: int | None = None,
        decode_responses: bool | None = None,
        client_name_suffix: str = "",
) -> aioredis.BlockingConnectionPool:
    kwargs: dict[str, Any] = dict(
        db=redis_pool_settings.db if db is None else db,
        username=redis_pool_settings.username,
        password=redis_pool_settings.password.get_secret_value() if redis_pool_settings.password else None,
        protocol=redis_pool_settings.protocol,
        decode_responses=redis_pool_settings.decode_responses if decode_responses is None else decode_responses,
        encoding=redis_pool_settings.encoding,
        encoding_errors=redis_pool_settings.encoding_errors,
        socket_connect_timeout=redis_pool_settings.socket_connection_timeout,
        socket_timeout=redis_pool_settings.socket_timeout,
        socket_keepalive=redis_pool_settings.socket_keepalive,
        socket_keepalive_options=_keep_alive_options(),
        health_check_interval=redis_pool_settings.health_check_interval,
        retry=build_retry(),
        retry_on_error=[RedisConnectionError, RedisTimeoutError, BusyLoadingError],
        client_name=f"{redis_pool_settings.client_name}{client_name_suffix}",
        lib_name=redis_pool_settings.lib_name,
        lib_version=redis_pool_settings.lib_version,
        max_connections=redis_pool_settings.max_connections,
        timeout=redis_pool_settings.pool_wait_timeout, # BlockingConnectionPool: wait for free conn
        maint_notifications_config=MaintNotificationsConfig(
            enabled=redis_pool_settings.maint_enabled,
            relaxed_timeout=redis_pool_settings.maint_relaxed_timeout,
            proactive_reconnect=redis_pool_settings.maint_proactive_reconnect,
        )
    )

    if redis_pool_settings.unix_socket_path:
        kwargs["path"] = redis_pool_settings.unix_socket_path
        kwargs["connection_class"] = aioredis.UnixDomainSocketConnection
    else:
        kwargs["host"] = redis_pool_settings.host
        kwargs["port"] = redis_pool_settings.port

    if redis_pool_settings.ssl:
        kwargs["connection_class"] = aioredis.SSLConnection
        kwargs.update(
            ssl_cert_reqs=redis_pool_settings.ssl_cert_reqs,
            ssl_ca_certs=redis_pool_settings.ssl_ca_certs,
            ssl_certfile=redis_pool_settings.ssl_certfile,
            ssl_keyfile=redis_pool_settings.ssl_keyfile,
            ssl_check_hostname=redis_pool_settings.ssl_check_hostname,
            ssl_min_version=redis_pool_settings.ssl_min_version,
        )

    return aioredis.BlockingConnectionPool(**kwargs)


def build_client(pool: aioredis.BlockingConnectionPool) -> aioredis.Redis:
    # client owns nothing; pool is closed explicitly (see lifespan management in main.py)
    return aioredis.Redis(connection_pool=pool, auto_close_connection_pool=False)

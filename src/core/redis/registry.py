from __future__ import annotations

from dataclasses import dataclass, field

import redis.asyncio as aioredis

from core.redis.client import build_pool, build_client
from core.config.settings import RedisSettings


@dataclass
class RedisRegistry:
    settings: RedisSettings
    pools: dict[str, aioredis.BlockingConnectionPool] = field(default_factory=dict)
    clients: dict[str, aioredis.Redis] = field(default_factory=dict)

    def _add(self, role: str, *, db: int, decode: bool, max_conn: int | None = None) -> None:
        s = self.settings.base
        if max_conn is not None:
            s = s.model_copy(update={"max_connections": max_conn})
        pool = build_pool(s, db=db, decode_responses=decode, client_name_suffix=f":{role}")

    async def start(self) -> None:
        ...

    async def stop(self) -> None:
        ...

    @property
    def cache(self) -> aioredis.Redis: return self.clients["cache"]
    @property
    def ratelimit(self) -> aioredis.Redis: return self.clients["ratelimit"]
    @property
    def leaderboard(self) -> aioredis.Redis: return self.clients["leaderboard"]
    @property
    def celery(self) -> aioredis.Redis: return self.clients["celery"]

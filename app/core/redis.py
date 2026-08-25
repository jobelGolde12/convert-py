from __future__ import annotations

import redis

from app.core.config import settings


_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        _redis_client.ping()
        return _redis_client
    except redis.RedisError:
        _redis_client = None
        return None

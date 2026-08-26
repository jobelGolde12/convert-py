from __future__ import annotations

import time

import redis

from app.core.config import settings


_redis_client: redis.Redis | None = None
_last_attempt: float = 0
_RETRY_INTERVAL = 30  # seconds between reconnection attempts


def get_redis() -> redis.Redis | None:
    global _redis_client, _last_attempt
    if _redis_client is not None:
        return _redis_client

    now = time.monotonic()
    if now - _last_attempt < _RETRY_INTERVAL:
        return None
    _last_attempt = now

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

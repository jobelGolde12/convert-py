from __future__ import annotations

import time
from collections import defaultdict, deque

from app.core.config import settings


class _WindowStore:
    def __init__(self) -> None:
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    def prune(self, key: str, cutoff: float) -> int:
        dq = self._windows.get(key)
        if not dq:
            return 0
        while dq and dq[0] < cutoff:
            dq.popleft()
        return len(dq)

    def add(self, key: str, now: float) -> None:
        self._windows[key].append(now)

    def pop_one(self, key: str) -> bool:
        dq = self._windows.get(key)
        if dq and dq:
            dq.popleft()
            return True
        return False


_mem = _WindowStore()


def _redis_client():
    from app.core.redis import get_redis

    return get_redis()


async def check_rate_limit(identity: str, window_seconds: int, limit: int) -> tuple[bool, int]:
    r = _redis_client()
    now = time.time()
    key = f"rl:{identity}:{window_seconds}"

    if r is not None:
        try:
            pipe = r.pipeline(transaction=True)
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            pipe.zadd(key, {f"{now}": now})
            pipe.zcard(key)
            pipe.pexpire(key, window_seconds * 1000 + 1000)
            results = pipe.execute()
            count = int(results[2] or 0)
            ok = count <= limit
            return ok, max(0, limit - count)
        except Exception:
            pass

    count = _mem.prune(key, now - window_seconds)
    _mem.add(key, now)
    count += 1
    return count <= limit, max(0, limit - count)


def _today_key(identity: str) -> str:
    from datetime import date

    return f"daily:{identity}:{date.today().isoformat()}"


def _mem_daily_count(day_key: str) -> int:
    # in-memory fallback stores timestamps; a "count" is one entry per conversion
    return _mem.prune(day_key, time.time() - 24 * 3600)


async def increment_daily(identity: str) -> tuple[bool, int]:
    r = _redis_client()
    day_key = _today_key(identity)

    if r is not None:
        try:
            count = int(r.incr(day_key) or 0)
            if count == 1:
                r.expire(day_key, 24 * 3600 + 60)
        except Exception:
            count = _mem_daily_count(day_key) + 1
            _mem.add(day_key, time.time())
    else:
        count = _mem_daily_count(day_key) + 1
        _mem.add(day_key, time.time())

    limit = settings.anon_conversions_per_day
    return count <= limit, max(0, limit - count)


async def read_daily(identity: str) -> int:
    r = _redis_client()
    day_key = _today_key(identity)

    if r is not None:
        try:
            value = r.get(day_key)
            return int(value) if value is not None else 0
        except Exception:
            pass

    return _mem_daily_count(day_key)


def decrement_daily(identity: str) -> None:
    """Roll back one daily-conversion unit. Safe to call from sync or async context."""
    import asyncio

    day_key = _today_key(identity)

    def _decr_sync() -> None:
        r = _redis_client()
        if r is not None:
            try:
                count = int(r.decr(day_key) or 0)
                if count < 0:
                    r.set(day_key, 0)
                return
            except Exception:
                pass
        _mem.pop_one(day_key)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and not loop.is_closed():
        # Called from within the event loop (e.g. BackgroundTasks): run inline,
        # the sync redis client does blocking I/O but this path is rare (failures).
        _decr_sync()
    else:
        _decr_sync()

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp. The database layer stores/returns naive UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

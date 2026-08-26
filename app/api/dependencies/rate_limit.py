from __future__ import annotations

import hashlib
import hmac

from fastapi import Request, Response

from app.services.quota_service import check_rate_limit, increment_daily
from app.core.config import settings

_COOKIE_NAME = "convert-guest-id"


class RateLimitGuard:
    def __init__(self, identity: str, *, remaining: int, limit: int) -> None:
        self.identity = identity
        self.remaining = remaining
        self.limit = limit


def _sign(value: str) -> str:
    """Return HMAC-SHA256 hex digest for *value*."""
    secret = (settings.secret_key or "dev").encode()
    return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()


def _anonymous_identity(request: Request) -> str:
    """Stable per-client identifier derived from IP + User-Agent.

    Used as the cookie value itself so the identity stays consistent even when
    the cookie cannot be delivered (e.g. error responses drop Set-Cookie).
    A server-side pepper prevents unhashing IPs from the stored value.
    """
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    digest = hashlib.sha256(f"{settings.secret_key}|{ip}|{ua}".encode()).hexdigest()[:24]
    return f"anon-{digest}"


async def guest_identity(request: Request, response: Response) -> str:
    raw_cookie = request.cookies.get(_COOKIE_NAME)
    if raw_cookie:
        # Verify HMAC signature to prevent cookie spoofing.
        parts = raw_cookie.split(".", 1)
        if len(parts) == 2:
            payload, sig = parts
            if hmac.compare_digest(sig, _sign(payload)):
                return payload
        # Invalid/tampered cookie — fall through to generate a new one.

    identity = _anonymous_identity(request)
    signed = f"{identity}.{_sign(identity)}"
    response.set_cookie(
        _COOKIE_NAME,
        signed,
        max_age=365 * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.is_prod,
    )
    return identity


async def enforce_rate_limit(request: Request, response: Response) -> RateLimitGuard | Response:
    identity = await guest_identity(request, response)

    allowed, remaining = await check_rate_limit(identity, 60, settings.anon_req_per_min)
    if not allowed:
        return Response(
            content='{"error":"RATE_LIMIT","message":"Too many requests"}',
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(settings.anon_req_per_min),
                "X-RateLimit-Remaining": "0",
                "Retry-After": "60",
            },
            media_type="application/json",
        )

    return RateLimitGuard(identity=identity, remaining=remaining, limit=settings.anon_req_per_min)


async def enforce_daily_quota(
    db, request: Request, response: Response
) -> RateLimitGuard | Response:
    identity = await guest_identity(request, response)
    allowed, remaining = await increment_daily(identity)
    if not allowed:
        return Response(
            content='{"error":"QUOTA_EXCEEDED","message":"Daily conversion limit reached"}',
            status_code=402,
            headers={"X-RateLimit-Remaining": "0"},
            media_type="application/json",
        )
    return RateLimitGuard(
        identity=identity, remaining=remaining, limit=settings.anon_conversions_per_day
    )

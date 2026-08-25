from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Response

from app.api.dependencies.rate_limit import guest_identity
from app.core.config import settings
from app.services.quota_service import read_daily

router = APIRouter()


@router.get("/quota")
async def get_quota(request: Request, response: Response):
    identity = await guest_identity(request, response)
    used = await read_daily(identity)
    limit = settings.anon_conversions_per_day
    remaining = max(0, limit - used)
    tomorrow = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    return {
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "resetsAt": tomorrow.isoformat(),
    }

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies.rate_limit import enforce_rate_limit, guest_identity
from app.api.schemas import JobCreateInput
from app.core.analytics import track_event
from app.core.clock import iso_now, utcnow
from app.core.conversions_catalog import find_conversion
from app.core.database import get_db, session_scope
from app.models.models import File, Job
from app.core.conversions_catalog import detect_format
from app.services.job_service import create_server_job, get_job_for_api, process_office_job

router = APIRouter()


@router.post("/")
async def create_job(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    body: JobCreateInput,
):
    guard = await enforce_rate_limit(request, response)
    if isinstance(guard, Response):
        return guard

    if len(body.tasks) != 1 or body.tasks[0].operation != "convert":
        raise HTTPException(status_code=422, detail="Invalid job payload")

    identity = guard.identity
    spec = body.tasks[0]

    file = db.get(File, spec.input)
    if not file:
        raise HTTPException(status_code=404, detail="Input file not found")
    if file.status not in {"ready", "done"}:
        raise HTTPException(
            status_code=409, detail=f"Input file is not ready (status: {file.status})"
        )

    source = detect_format(file.filename, file.mime_type)
    if not source:
        raise HTTPException(status_code=415, detail="Could not detect source format")

    conversion = find_conversion(source, spec.outputFormat)
    if not conversion:
        raise HTTPException(
            status_code=422, detail=f"No conversion from {source} to {spec.outputFormat}"
        )
    if conversion.location != "server":
        raise HTTPException(
            status_code=422, detail="Conversion runs in the browser and never reaches the server"
        )

    job, conversion_used = create_server_job(
        db,
        [
            {
                "operation": spec.operation,
                "input": spec.input,
                "outputFormat": spec.outputFormat,
                "options": spec.options,
            }
        ],
        guest_id=identity,
    )
    background_tasks.add_task(process_office_job, job.id, identity)

    return {
        "id": job.id,
        "status": job.status,
        "conversion": {
            "id": conversion_used.id,
            "label": conversion_used.label,
            "location": conversion_used.location,
        },
        "createdAt": job.created_at.isoformat() if job.created_at else iso_now(),
    }


@router.get("/")
async def list_jobs(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
    cursor: str | None = None,
):
    guard = await enforce_rate_limit(request, response)
    if isinstance(guard, Response):
        return guard

    identity = guard.identity
    limit = min(max(limit, 1), 50)

    query = (
        db.query(Job)
        .options(selectinload(Job.tasks))  # avoid N+1 lazy loads per job
        .filter(Job.guest_id == identity)
    )
    if cursor:
        ts_str, _, cursor_id = cursor.partition(":")
        try:
            ts = int(ts_str)
        except ValueError:
            ts = 0
        # DB stores naive UTC datetimes; compare with naive to avoid tz mismatches.
        cursor_dt = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
        if cursor_id:
            query = query.filter(
                (Job.created_at < cursor_dt)
                | ((Job.created_at == cursor_dt) & (Job.id < cursor_id))
            )

    jobs = query.order_by(Job.created_at.desc(), Job.id.desc()).limit(limit + 1).all()
    has_more = len(jobs) > limit
    page = jobs[:limit]

    def serialize(j: Job):
        return {
            "id": j.id,
            "status": j.status,
            "error": {"code": j.error_code, "message": j.error_message} if j.error_code else None,
            "createdAt": j.created_at.isoformat() if j.created_at else None,
            "tasks": [
                {"id": t.id, "operation": t.operation, "status": t.status, "progress": t.progress}
                for t in (j.tasks or [])
            ],
        }

    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = f"{int(last.created_at.timestamp())}:{last.id}"

    return {"jobs": [serialize(j) for j in page], "nextCursor": next_cursor}


def _owned_job_or_404(db: Session, job_id: str, identity: str | None) -> Job | None:
    """Return the job when it exists and belongs to this guest (or has no owner)."""
    job = db.get(Job, job_id)
    if not job:
        return None
    if job.guest_id and identity and job.guest_id != identity:
        return None
    return job


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    identity = await guest_identity(request, response)
    job = _owned_job_or_404(db, job_id, identity)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return get_job_for_api(db, job_id)


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    identity = await guest_identity(request, response)
    job = _owned_job_or_404(db, job_id, identity)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in {"done", "error", "cancelled"}:
        return {"id": job.id, "status": job.status, "cancelled": False}

    job.status = "cancelled"
    job.ended_at = utcnow()
    for task in job.tasks or []:
        task.status = "cancelled"
        task.ended_at = utcnow()
    db.commit()
    track_event("job_cancelled", job_id=job.id)
    return {"id": job.id, "status": "cancelled", "cancelled": True}


@router.get("/{job_id}/events")
async def job_events(
    job_id: str,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    identity = await guest_identity(request, response)
    job = _owned_job_or_404(db, job_id, identity)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_payload = None
        try:
            while True:
                with session_scope() as poll_db:
                    current = get_job_for_api(poll_db, job_id)
                if not current:
                    break
                payload = json.dumps(current)
                if payload != last_payload:
                    last_payload = payload
                    yield f"event: job\ndata: {payload}\n\n"
                if current["status"] in {"done", "error", "cancelled"}:
                    break
                await asyncio.sleep(0.6)
                if await request.is_disconnected():
                    break
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "Connection": "keep-alive"},
    )

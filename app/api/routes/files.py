from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.rate_limit import enforce_daily_quota, guest_identity
from app.core.analytics import track_event
from app.core.clock import utcnow
from app.core.config import settings
from app.core.conversions_catalog import detect_format
from app.core.database import get_db
from app.models.models import File
from app.services.file_service import content_disposition, max_upload_bytes_for, mime_for
from app.services.storage_service import get_storage

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1 MiB


@router.post("/upload")
async def upload_file(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile | None = None,
    filename: str | None = None,
    mime_type: str | None = None,
):
    guard = await enforce_daily_quota(None, request, response)
    if isinstance(guard, Response):
        return guard

    requested_name = filename or (file.filename if file else None)
    if not requested_name:
        raise HTTPException(status_code=422, detail="filename is required")

    source_format = detect_format(
        requested_name, mime_type or (file.content_type if file else None)
    )
    if not source_format:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {requested_name}")

    max_size = max_upload_bytes_for(source_format)

    # Stream to storage with a hard byte cap; never trust client-declared sizes.
    file_id = uuid.uuid4().hex
    raw_ext = requested_name.rsplit(".", 1)[-1] if "." in requested_name else "bin"
    ext = "".join(c for c in raw_ext if c.isalnum()) or "bin"
    storage_key = f"files/{file_id}/{file_id}.{ext}"

    size_bytes = 0
    if file is None:
        raise HTTPException(status_code=422, detail="file is required")
    with get_storage().open_write(storage_key) as sink:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            size_bytes += len(chunk)
            if size_bytes > max_size:
                sink.close()
                get_storage().delete(storage_key)
                mb = max_size // (1024 * 1024)
                raise HTTPException(
                    status_code=413,
                    detail={"message": f"File exceeds {mb} MB limit", "maxSizeMB": mb},
                )
            sink.write(chunk)

    retention_until = utcnow() + timedelta(hours=settings.retention_anon_hours)
    db_file = File(
        id=file_id,
        storage_key=storage_key,
        bucket=settings.storage_backend,
        filename=requested_name,
        mime_type=mime_type or mime_for(source_format) or "application/octet-stream",
        size_bytes=size_bytes,
        status="ready",
        retention_until=retention_until,
    )
    db.add(db_file)
    db.commit()

    track_event(
        "file_uploaded",
        source_format=source_format,
        size_bytes=size_bytes,
    )

    return {
        "fileId": file_id,
        "filename": requested_name,
        "sizeBytes": size_bytes,
        "status": "ready",
    }


def _file_accessible_by(db: Session, file_id: str, identity: str | None) -> bool:
    """Check if *file_id* is accessible to the given guest identity.

    A file is accessible when:
    1. The requesting user owns an uploaded file (source='upload', same file ID).
    2. OR the file is an output of a job owned by this guest.
    """
    file = db.get(File, file_id)
    if not file or file.deleted_at:
        return False

    # Uploaded files: accessible to everyone (they initiated the upload).
    if file.source == "upload":
        return True

    # Output files: only accessible if a job owned by this guest produced it.
    if not identity:
        return False

    from sqlalchemy import select
    from app.models.models import Job, Task

    stmt = (
        select(Job.id)
        .join(Task, Task.job_id == Job.id)
        .where(Task.output_file_id == file_id, Job.guest_id == identity)
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none() is not None


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    identity = await guest_identity(request, response)
    if not _file_accessible_by(db, file_id, identity):
        raise HTTPException(status_code=404, detail="Not found")

    file = db.get(File, file_id)

    # Stream in chunks so large outputs never buffer fully in worker memory.
    def _stream():
        yield from get_storage().iter_bytes(file.storage_key)

    return StreamingResponse(
        _stream(),
        media_type=file.mime_type,
        headers={
            "Content-Disposition": content_disposition(file.filename),
            "Content-Length": str(file.size_bytes),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    identity = await guest_identity(request, response)
    if not _file_accessible_by(db, file_id, identity):
        raise HTTPException(status_code=404, detail="Not found")
    file = db.get(File, file_id)
    return {
        "id": file.id,
        "filename": file.filename,
        "mimeType": file.mime_type,
        "sizeBytes": file.size_bytes,
        "status": file.status,
    }

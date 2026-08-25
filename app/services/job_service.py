from __future__ import annotations

import json
import os
import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.core.database import session_scope
from app.core.exceptions import (
    ConflictStateError,
    InvalidDataError,
    NotFoundError,
    OfficeError,
    UnsupportedConversionError,
    UnsupportedFormatError,
)
from app.models.models import Conversion, File, Job, Task
from app.core.conversions_catalog import CONVERSIONS, detect_format, extension_for
from app.services.conversion_service import (
    convert_with_soffice,
    markdown_to_html,
    sha256,
    validate_output,
)
from app.services.file_service import mime_for
from app.services.storage_service import get_storage


def get_conversion(source: str, target: str) -> Any | None:
    for c in CONVERSIONS:
        if source in c.from_ and c.to == target:
            return c
    return None


def create_server_job(
    db: Session,
    tasks: list[dict[str, Any]],
    *,
    guest_id: str | None = None,
    idempotency_key: str | None = None,
) -> tuple[Job, Any]:
    if len(tasks) != 1 or tasks[0].get("operation") != "convert":
        raise InvalidDataError("MVP supports exactly one convert task per job")

    spec = tasks[0]
    file = db.get(File, spec["input"])
    if not file:
        raise NotFoundError("Input file not found")
    if file.status not in {"ready", "done"}:
        raise ConflictStateError(f"Input file is not ready (status: {file.status})")

    source = detect_format(file.filename, file.mime_type)
    if not source:
        raise UnsupportedFormatError("Could not detect source format")

    conversion = get_conversion(source, spec["outputFormat"])
    if not conversion:
        raise UnsupportedConversionError(f"No conversion from {source} to {spec['outputFormat']}")
    if conversion.location != "server":
        raise UnsupportedConversionError(
            f'"{conversion.id}" runs in the browser and never reaches the server'
        )

    job = Job(
        guest_id=guest_id,
        idempotency_key=idempotency_key,
        status="queued",
        timings_ms=json.dumps({"enqueueMs": 0}),
    )
    db.add(job)
    db.flush()

    task = Task(
        job_id=job.id,
        operation="convert",
        engine=conversion.engine,
        engine_version="libreoffice-24.2",
        input_file_id=file.id,
        options=json.dumps({**(spec.get("options") or {}), "outputFormat": conversion.to}),
        status="waiting",
    )
    db.add(task)
    db.commit()
    db.refresh(job)
    return job, conversion


def _set_task_progress(db: Session, task_id: str, progress: int) -> None:
    db.execute(update(Task).where(Task.id == task_id).values(progress=progress))
    db.commit()


def _fail_job(
    db: Session,
    job_id: str,
    task_id: str | None,
    code: str,
    message: str,
    guest_id: str | None,
) -> None:
    if task_id:
        db.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(
                status="error",
                error_code=code,
                error_message=message[:500],
                ended_at=utcnow(),
            ),
        )
    db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status="error",
            error_code=code,
            error_message=message[:500],
            ended_at=utcnow(),
        ),
    )
    db.commit()
    if guest_id:
        from app.services.quota_service import decrement_daily

        try:
            decrement_daily(guest_id)
        except Exception:
            pass


def process_office_job(job_id: str, guest_id: str | None = None) -> None:
    with session_scope() as db:
        job = db.get(Job, job_id)
        if not job:
            raise NotFoundError("Job not found")
        if job.status == "cancelled":
            return
        if job.status != "queued":
            return

        task = db.execute(select(Task).where(Task.job_id == job_id)).scalar_one_or_none()
        if not task:
            _fail_job(db, job_id, None, "OPEN_FAILED", "Input file missing", guest_id)
            return

        input_file = db.get(File, task.input_file_id)
        if not input_file:
            _fail_job(db, job_id, task.id, "OPEN_FAILED", "Input file missing", guest_id)
            return

        job.status = "processing"
        job.started_at = utcnow()
        task.status = "processing"
        task.started_at = utcnow()
        task.progress = 10
        db.commit()

        source = detect_format(input_file.filename, input_file.mime_type) or "unknown"
        parsed = json.loads(task.options or "{}") if task.options else {}
        target = parsed.get("outputFormat", "pdf")
        conversion = get_conversion(source, target)
        if not conversion:
            _fail_job(
                db,
                job_id,
                task.id,
                "UNSUPPORTED_CONVERSION",
                f"No conversion from {source} to {target}",
                guest_id,
            )
            return

        tmp = os.path.join(settings.lo_profile_root, f"convert-{job_id}-{uuid.uuid4().hex}")
        out_dir = os.path.join(tmp, "out")
        os.makedirs(out_dir, exist_ok=True)
        output_path: str | None = None
        out_id: str | None = None
        storage_key: str | None = None

        try:
            _set_task_progress(db, task.id, 20)

            storage = get_storage()
            input_buf = storage.get_bytes(input_file.storage_key)
            ext = input_file.filename.rsplit(".", 1)[-1] if "." in input_file.filename else "bin"
            input_path = os.path.join(tmp, f"input.{ext}")
            with open(input_path, "wb") as f:
                f.write(input_buf)

            if source == "md" and target == "pdf":
                html = markdown_to_html(input_buf.decode("utf-8"))
                html_path = os.path.join(tmp, "input.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html)
                _set_task_progress(db, task.id, 45)
                res = convert_with_soffice(
                    html_path, out_dir, target, timeout_ms=settings.lo_timeout_ms
                )
            else:
                _set_task_progress(db, task.id, 45)
                res = convert_with_soffice(
                    input_path, out_dir, target, timeout_ms=settings.lo_timeout_ms
                )

            output_path = res.output_path
            _set_task_progress(db, task.id, 70)

            with open(output_path, "rb") as fh:
                out_buf = fh.read()
            validate_output(target, out_buf)
            out_id = str(uuid.uuid4())
            storage_key = f"files/{out_id}/{out_id}.{extension_for(target)}"
            storage.put_bytes(storage_key, out_buf)
            _set_task_progress(db, task.id, 85)

            out_file = File(
                id=out_id,
                storage_key=storage_key,
                bucket="convert-files",
                filename=input_file.filename.rsplit(".", 1)[0] + "." + extension_for(target),
                mime_type=mime_for(target),
                size_bytes=len(out_buf),
                checksum_sha256=sha256(out_buf),
                status="done",
                source="output",
                retention_until=utcnow(),
            )
            db.add(out_file)

            job.credits_charged = conversion.priceCredits
            job.ended_at = utcnow()
            job.status = "done"
            elapsed = (
                int((job.ended_at - job.started_at).total_seconds() * 1000) if job.started_at else 0
            )
            job.timings_ms = json.dumps({"engineMs": elapsed})

            # conditional finalize so a concurrent cancel cannot race us
            finished = db.execute(
                update(Job)
                .where(Job.id == job_id, Job.status.notin_(["cancelled", "error"]))
                .values(
                    status="done",
                    ended_at=job.ended_at,
                    credits_charged=conversion.priceCredits,
                    timings_ms=job.timings_ms,
                )
            )
            if finished.rowcount == 0:
                raise ConflictStateError("Job was cancelled during processing")

            db.add(
                Conversion(
                    user_id=job.user_id,
                    job_id=job_id,
                    source_format=source,
                    target_format=target,
                    engine=conversion.engine,
                    location=conversion.location,
                    status="done",
                    input_bytes=input_file.size_bytes,
                    output_bytes=len(out_buf),
                    duration_ms=elapsed,
                    credits_used=conversion.priceCredits,
                )
            )

            task.status = "finished"
            task.progress = 100
            task.ended_at = utcnow()
            task.output_file_id = out_id
            db.commit()
        except Exception as exc:
            code = exc.code if isinstance(exc, OfficeError) else "CONVERSION_FAILED"
            message = str(exc)[:500]
            _fail_job(db, job_id, task.id, code, message, guest_id)
            if out_id and storage_key:
                try:
                    db.delete(db.get(File, out_id))
                    get_storage().delete(storage_key)
                except Exception:
                    pass
            # Failure state is persisted above; do not re-raise inside BackgroundTasks.
            return
        finally:
            for root_d, _, files in os.walk(tmp):
                for f in files:
                    try:
                        os.remove(os.path.join(root_d, f))
                    except OSError:
                        pass
            try:
                os.removedirs(tmp)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Query / cancel
# ---------------------------------------------------------------------------

# keep the API-facing dict shape aligned with the TypeScript `JobApi` type.


def get_job_for_api(db: Session, job_id: str) -> dict[str, Any] | None:
    job = db.get(Job, job_id)
    if not job:
        return None

    progress = 0
    if job.tasks:
        progress = max((t.progress for t in job.tasks), default=0)
    if job.status == "done":
        progress = 100

    outputs = []
    for t in job.tasks or []:
        if t.output_file_id and t.output:
            out = t.output
            outputs.append(
                {
                    "fileId": out.id,
                    "filename": out.filename,
                    "sizeBytes": out.size_bytes,
                    "downloadUrl": f"/api/v1/files/{out.id}/download",
                    "expiresAt": utcnow().isoformat(),
                }
            )

    return {
        "id": job.id,
        "status": job.status,
        "progress": progress,
        "error": {"code": job.error_code, "message": job.error_message} if job.error_code else None,
        "creditsCharged": job.credits_charged,
        "createdAt": job.created_at.isoformat() if job.created_at else None,
        "startedAt": job.started_at.isoformat() if job.started_at else None,
        "endedAt": job.ended_at.isoformat() if job.ended_at else None,
        "tasks": [
            {
                "id": t.id,
                "operation": t.operation,
                "engine": t.engine,
                "status": t.status,
                "progress": t.progress,
                "error": {"code": t.error_code, "message": t.error_message}
                if t.error_code
                else None,
            }
            for t in (job.tasks or [])
        ],
        "outputs": outputs,
    }

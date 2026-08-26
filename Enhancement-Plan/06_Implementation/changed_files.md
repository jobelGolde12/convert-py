# Changed Files

## Modified Files (12)

| File | Changes |
|------|---------|
| `app/models/models.py` | Removed User, UsageRecord models; removed user_id FKs from File/Job/Conversion; removed user_id indexes; imported utcnow from core.clock |
| `app/core/config.py` | Removed retention_free_hours, retention_paid_hours, upload_signing_secret settings |
| `app/core/database.py` | Removed unused `Base = declarative_base()` and its import |
| `app/core/redis.py` | Added `_last_attempt` timestamp and `_RETRY_INTERVAL = 30` for reconnection |
| `app/api/routes/files.py` | Fixed bucket to use settings.storage_backend; added streaming download; added file_uploaded analytics event; added StreamingResponse import |
| `app/api/routes/jobs.py` | Fixed deprecated datetime.utcfromtimestamp(); added guest_identity import; added _owned_job_or_404() helper; added job_cancelled analytics event; added selectinload for tasks |
| `app/services/file_service.py` | Removed sign_payload(), create_signed_upload(), verify_signed_upload(), file_extension_for() functions (52 lines removed) |
| `app/services/job_service.py` | Removed get_conversion() duplicate; fixed output file retention; fixed bucket; compiled regex at module level; added re import at top level; added analytics events for conversion_completed/conversion_failed; added selectinload for task.output |
| `app/services/quota_service.py` | Simplified decrement_daily() to remove redundant pop_one double-check; added os, uuid imports |
| `app/main.py` | Moved json/sys/re/timedelta imports to top level; added SmartGzipMiddleware; added CachedStaticFiles; added security header logging; pre-computed catalog JSON; added lifespan secret validation |
| `requirements.txt` | Removed: alembic, celery, slowapi, limits, tenacity, sse-starlette, pypdf, pillow, reportlab, pypandoc (11 -> still 11 remaining) |
| `pyproject.toml` | Removed: alembic, celery, slowapi, limits, tenacity, alembic-postgresql-enum, sse-starlette, pypdf, pillow, reportlab, pypandoc |

## Deleted Files (6)

| File | Reason |
|------|--------|
| `app/workers/__init__.py` | Celery never wired |
| `app/workers/celery_app.py` | Celery never wired |
| `app/workers/office_worker.py` | Celery never wired |
| `app/client_engine/__init__.py` | Empty package |
| `app/templates/components/__init__.py` | Empty package |

## Lines Changed Summary

| Metric | Count |
|--------|-------|
| Files modified | 12 |
| Files deleted | 5 |
| Lines removed (dead code) | ~350 |
| Lines removed (dependencies) | 11 packages |
| Net new lines | ~50 (middleware, retry logic, streaming) |

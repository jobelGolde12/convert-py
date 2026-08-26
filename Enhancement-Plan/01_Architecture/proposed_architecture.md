# Proposed Architecture (Post-Enhancement)

## Changes Applied

The architecture remains structurally identical — no new modules, no new dependencies, no new patterns. All changes are internal corrections and dead-code removal within the existing structure.

### Data Model — Simplified

```
File       — no user_id FK, bucket from settings, correct retention
Job        — no user_id FK, guest-only
Task       — unchanged
Conversion — no user_id FK
```

Removed tables: `users`, `usage_records`.

### Config — Cleaned

```
retention_anon_hours     — used (default 1h)
retention_free_hours     — removed (unused)
retention_paid_hours     — removed (unused)
upload_signing_secret    — removed (unused)
```

### Dependency Tree — Reduced

```
Before (22):  + celery, slowapi, limits, tenacity, alembic,
                alembic-postgresql-enum, sse-starlette, pypdf,
                pillow, reportlab, pypandoc

After  (11):  fastapi, uvicorn, jinja2, sqlalchemy, redis,
              pydantic, pydantic-settings, python-multipart,
              aiofiles, python-dotenv, boto3
```

### File Structure — Trimmed

Removed:
- `app/workers/celery_app.py` (Celery never wired)
- `app/workers/office_worker.py`
- `app/client_engine/__init__.py` (empty)
- `app/templates/components/__init__.py` (empty)

### Redis — Resilient

`get_redis()` now retries connection attempts after 30 seconds instead of permanently returning `None` after the first transient failure.

### No Changes To

- Page routes (/, /convert, /privacy, /terms, /404)
- API contract (all endpoints, schemas unchanged)
- Frontend (templates, static assets)
- Test suite (43 tests, all passing)
- Middleware stack (CORS, gzip, security headers)
- Conversion pipeline (LibreOffice subprocess)

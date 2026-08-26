# Performance Comparison

## Before vs After

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Production dependencies | 22 | 11 | -50% |
| Empty packages | 3 | 0 | -3 |
| Unused config settings | 3 | 0 | -3 |
| Dead code lines | ~350 | 0 | -350 |
| Tests passing | 43 | 43 | 0 |
| Ruff warnings | 0 | 0 | 0 |

## Dependency Comparison

### Before (22 packages)

```
fastapi, uvicorn, jinja2, sqlalchemy, alembic, redis, celery,
pydantic, pydantic-settings, python-multipart, aiofiles, sse-starlette,
pypdf, pillow, reportlab, pypandoc, boto3, python-dotenv,
slowapi, limits, tenacity, alembic-postgresql-enum
```

### After (11 packages)

```
fastapi, uvicorn, jinja2, sqlalchemy, redis, pydantic,
pydantic-settings, python-multipart, aiofiles, python-dotenv, boto3
```

### Removed (11 packages)

| Package | Reason |
|---------|--------|
| celery | Workers never wired; no task queue |
| slowapi | Rate limiting implemented manually with Redis |
| limits | Rate limiting uses raw Redis sorted sets |
| tenacity | No retry logic in application code |
| alembic | No migrations; init_db uses create_all |
| alembic-postgresql-enum | No PostgreSQL enum support needed |
| sse-starlette | SSE implemented with raw StreamingResponse |
| pypdf | PDF processing runs client-side or via LibreOffice |
| pillow | Image processing runs client-side |
| reportlab | PDF generation runs client-side |
| pypandoc | Document conversion uses LibreOffice directly |

## Performance Impact

### Startup Time

Fewer dependencies = faster `pip install` and smaller container image. No measurable startup time change (all removed packages were unused at runtime).

### Request Latency

| Endpoint | Change | Expected Impact |
|----------|--------|-----------------|
| `/convert` | Pre-computed catalog JSON | ~0.1ms saved per request |
| `/api/v1/files/{id}/download` | Streaming response | Lower TTFB, constant memory |
| `/api/v1/jobs/` (list) | selectinload tasks | Fewer DB round-trips (N+1 eliminated) |
| `/api/v1/jobs/{id}` | selectinload tasks+output | Fewer DB round-trips |
| Error paths | Regex pre-compiled | Negligible (error path only) |

### Memory Usage

- Streaming downloads avoid buffering entire files
- Fewer import-time module loads (11 fewer packages)
- No change to working set size for normal request processing

### Resilience

- Redis reconnection retry (30s interval) prevents permanent fallback to in-memory rate limiting after transient failures

## What Did NOT Change

- Database schema (no migrations)
- API contract (endpoints, request/response formats)
- Frontend templates and assets
- Test suite
- Conversion pipeline (LibreOffice subprocess)
- Security model (guest-only, HMAC cookies)

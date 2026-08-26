# Current Architecture

## Stack

- **Framework**: FastAPI 0.111+ with uvicorn
- **Database**: SQLite via SQLAlchemy 2.0 (naive UTC datetimes)
- **Cache/Rate Limiting**: Redis with in-memory fallback
- **Templates**: Jinja2 server-rendered pages
- **Conversion Engine**: LibreOffice (soffice) via subprocess
- **Storage**: Local filesystem or R2/S3 (configurable via `storage_backend`)

## Application Structure

```
app/
  core/          config, clock, redis, analytics, conversions_catalog, database, exceptions, logger
  models/        SQLAlchemy ORM: File, Job, Task, Conversion
  api/routes/    files, jobs, formats, quota
  api/dependencies/  rate_limit (guest identity, HMAC cookies)
  services/      file_service, job_service, quota_service, storage_service, conversion_service
  main.py        App factory, middleware, page routes, lifespan
  static/        CSS, JS, favicon
  templates/     Jinja2: index, convert, privacy, terms, 404
```

## Data Model

| Table | Purpose |
|-------|---------|
| `files` | Uploaded and output files with retention timestamps |
| `jobs` | Conversion job lifecycle (queued -> processing -> done/error/cancelled) |
| `tasks` | Individual conversion steps within a job |
| `conversions` | Completed conversion audit log |

## Request Flow

1. Upload file -> `POST /api/v1/files/upload` (quota enforced, streamed to storage)
2. Create job -> `POST /api/v1/jobs/` (rate limited, background task dispatched)
3. Background task runs LibreOffice -> writes output to storage, updates DB
4. SSE polling -> `GET /api/v1/jobs/{id}/events` (0.6s interval)
5. Download result -> `GET /api/v1/files/{id}/download` (streamed via StreamingResponse)

## Key Design Decisions

- **Guest-only auth**: No user accounts; identity via HMAC-signed cookie (IP+User-Agent + pepper)
- **TTL-based cleanup**: Files use `retention_until` (default 1h for anon) instead of immediate expiry
- **Streaming responses**: File downloads use `StreamingResponse` to avoid buffering large files in memory
- **Pre-computed catalog**: Convert page JSON computed once at startup, not per-request
- **Gzip middleware**: `SmartGzipMiddleware` compresses JSON/HTML responses, skips SSE streams

## Production Dependencies (11 total)

fastapi, uvicorn, jinja2, sqlalchemy, redis, pydantic, pydantic-settings, python-multipart, aiofiles, python-dotenv, boto3

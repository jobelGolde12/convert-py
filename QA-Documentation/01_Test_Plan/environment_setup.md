# Environment Setup

## Operating Environment

| Item | Value |
|------|-------|
| OS | Linux |
| Python | 3.12 |
| Package Manager | pip (with venv) |
| Virtual Environment | `venv/` |

## Dependency Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Environment Variables (from `.env.example`)

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_NAME` | No | Application display name |
| `APP_URL` | No | Base URL for canonical links and sitemap |
| `ENV` | No | `development`, `staging`, or `production` |
| `SECRET_KEY` | Yes (prod) | HMAC signing key for cookies |
| `UPLOAD_SECRET` | Yes (prod) | Upload authentication secret |
| `TURSO_DATABASE_URL` | No | Turso/libSQL database URL |
| `TURSO_AUTH_TOKEN` | No | Turso authentication token |
| `DATABASE_URL` | No | Local SQLite fallback URL |
| `REDIS_URL` | No | Redis connection URL |
| `RETENTION_ANON_HOURS` | No | File retention period (hours) |
| `ANON_CONVERSIONS_PER_DAY` | No | Daily conversion limit per guest |
| `ANON_REQ_PER_MIN` | No | Rate limit per minute |
| `LO_CONCURRENCY` | No | LibreOffice concurrency limit |
| `LO_TIMEOUT_MS` | No | LibreOffice timeout (ms) |
| `LO_PROFILE_ROOT` | No | LibreOffice profile directory |
| `R2_ACCOUNT_ID` | No | Cloudflare R2 account ID |
| `R2_ACCESS_KEY_ID` | No | R2 access key |
| `R2_SECRET_ACCESS_KEY` | No | R2 secret key |
| `R2_BUCKET` | No | R2 bucket name |
| `R2_PUBLIC_URL` | No | R2 public URL |
| `STORAGE_BACKEND` | No | `local`, `r2`, or `s3` |
| `LOCAL_STORAGE_ROOT` | No | Local file storage path |
| `CORS_ORIGINS` | No | Allowed CORS origins (JSON list) |

## Test Configuration

Tests automatically configure isolated environment:
- SQLite database in temp directory
- Local file storage in temp directory
- Redis mocked to unreachable (triggers in-memory fallback)
- In-memory rate limit and quota stores reset between tests
- Database tables truncated between tests via `_isolated_db` fixture

## Running Tests

```bash
./venv/bin/python -m pytest tests/ -v
```

## Running Lint

```bash
./venv/bin/python -m ruff check app tests
```

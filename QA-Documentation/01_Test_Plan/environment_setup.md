# Environment Setup

## Operating Environment

- OS: Linux (Ubuntu-based)
- Python: 3.12.3
- Virtual Environment: venv/ (project-local)

## Package Manager

- pip (standard Python package manager)
- Dependencies managed via `requirements.txt` and `requirements-dev.txt`
- Build system: Hatchling (pyproject.toml)

## Dependency Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Development Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Build Process

No frontend build step required. Static CSS and JS served directly.

## Database Setup

SQLite database created automatically on first run via `init_db()`.
Alembic is scaffolded but no migration files exist yet.

## Test Execution

```bash
pytest tests/ -v          # Run all tests
ruff check app tests      # Lint
```

## Environment Variable Names (from .env.example)

| Variable | Purpose | Required |
|----------|---------|----------|
| APP_NAME | Application display name | No (has default) |
| APP_URL | Public URL | No (has default) |
| ENV | Environment (development/staging/production) | No (has default) |
| SECRET_KEY | Secret pepper for identity hashing | Yes |
| UPLOAD_SECRET | HMAC signing secret for uploads | Yes |
| DATABASE_URL | SQLAlchemy database URL | No (has default) |
| REDIS_URL | Redis connection URL | No (has default) |
| RETENTION_ANON_HOURS | File retention for anonymous users | No |
| RETENTION_FREE_HOURS | File retention for free users | No |
| RETENTION_PAID_HOURS | File retention for paid users | No |
| ANON_CONVERSIONS_PER_DAY | Daily conversion limit | No |
| ANON_REQ_PER_MIN | Per-minute rate limit | No |
| LO_CONCURRENCY | LibreOffice concurrency | No |
| LO_TIMEOUT_MS | LibreOffice timeout | No |
| LO_PROFILE_ROOT | LibreOffice profile directory | No |
| R2_ACCOUNT_ID | Cloudflare R2 account ID | No |
| R2_ACCESS_KEY_ID | R2 access key | No |
| R2_SECRET_ACCESS_KEY | R2 secret key | No |
| R2_BUCKET | R2 bucket name | No |
| R2_PUBLIC_URL | R2 public URL | No |
| CORS_ORIGINS | Allowed CORS origins (JSON list) | No |

**Note:** Secret values are never documented. Only variable names are listed.

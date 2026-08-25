# Convert-Py

Document conversion platform built with Python and FastAPI — server-rendered web UI,
REST API, background conversion pipeline, and tests. A rewrite of the original
Convert platform (TypeScript) with a fully working converter out of the box.

## Overview

Convert-Py lets users convert documents, spreadsheets, presentations, images, and
text between formats without an account. Files are uploaded through the web UI or
REST API, queued as conversion jobs, processed by a headless LibreOffice engine
(or entirely in-browser for client-side tools), and made available for download
until retention expires.

Anonymous usage is controlled by per-guest daily quotas and rate limits, backed by
Redis with an automatic in-memory fallback when Redis is unavailable.

## Features

### Server-side conversions

- LibreOffice headless engine (`soffice`) for document formats:
  PDF, DOCX/DOC, XLSX/XLS/CSV, PPTX/PPT, RTF, EPUB, HTML, TXT
- Markdown → HTML/PDF pipeline with a custom, XSS-safe Markdown renderer and
  print-ready styling
- Output validation (magic-byte checks for PDF / Office Open XML / HTML)
- Per-job task tracking with progress, error codes, cancellation, and SSE
  live progress streaming

### Client-side tools (run in the browser, never uploaded)

- Merge PDF, split PDF, watermark PDF, compress PDF
- PDF → Text / Markdown / Image extraction
- Image → PDF

### Platform

- Working web UI: landing page, converter (upload → progress → download),
  privacy and terms pages
- REST API v1 with auto-generated Swagger docs at `/docs`
- Anonymous guest identity (cookie derived from a salted IP + User-Agent hash)
- Daily conversion quota and per-minute rate limiting (Redis, in-memory fallback)
- Retention tiers by account type (anonymous 1 h, free 24 h, paid 7 days)
- Pluggable storage backend: local disk or Cloudflare R2 (S3-compatible)
- SEO basics: canonical URLs from `APP_URL`, generated `robots.txt` and `sitemap.xml`
- Security headers on every response (nosniff, frame-deny, referrer policy,
  HSTS in production)

## Technology Stack

| Layer      | Technology |
| ---------- | ---------- |
| Framework  | FastAPI, Uvicorn |
| UI         | Jinja2 server-rendered templates, vanilla JS/CSS |
| Validation | Pydantic v2 + pydantic-settings |
| Database   | SQLAlchemy 2.0, SQLite by default |
| Storage    | Local disk; Cloudflare R2 via boto3 (optional) |
| Quotas     | Redis (in-memory fallback) |
| Engine     | LibreOffice headless (`soffice`), pypdf |
| Tooling    | pytest, ruff, mypy, Docker Compose |

## Requirements

- Python **3.11+**
- [LibreOffice](https://www.libreoffice.org/) headless — required for all
  server-side conversions
  - Debian/Ubuntu: `sudo apt install libreoffice libreoffice-writer`
  - macOS: `brew install --cask libreoffice`
- Redis (optional — quotas fall back to in-memory tracking when unreachable)

## Getting Started

```bash
git clone <repository>
cd convert-py

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt   # or: make install

cp .env.example .env    # adjust as needed

uvicorn app.main:app --reload    # or: make dev
```

The app creates its database tables automatically on startup (`init_db` runs in
the FastAPI lifespan). Then open <http://localhost:8000>.

> **Note:** the end-to-end conversion test is skipped automatically if
> `soffice` is not on your `PATH`. Install LibreOffice to exercise real
> conversions locally.

## Environment Configuration

Copy `.env.example` to `.env`. All settings are read from the environment /
`.env` via pydantic-settings. Defaults work out of the box for local
development.

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `APP_NAME` | No | Application name used in templates and OpenAPI title |
| `APP_URL` | No | Canonical base URL; drives sitemap and robots.txt |
| `ENV` | No | `development` / `staging` / `production`; enables HSTS when `production` |
| `SECRET_KEY` | Yes in prod | Signs guest identity hashes — set a strong random value |
| `UPLOAD_SECRET` | Yes in prod | Upload signing secret — change from the dev default |
| `DATABASE_URL` | No | SQLAlchemy URL; default `sqlite:///./dev.db` |
| `REDIS_URL` | No | Redis connection; quotas fall back to memory if down |
| `RETENTION_ANON_HOURS` | No | File retention for anonymous guests (default 1) |
| `RETENTION_FREE_HOURS` / `RETENTION_PAID_HOURS` | No | Retention for free/paid tiers (24 h / 7 days) |
| `ANON_CONVERSIONS_PER_DAY` | No | Daily quota per anonymous guest (default 5) |
| `ANON_REQ_PER_MIN` | No | Per-minute request limit (default 60) |
| `LO_CONCURRENCY` | No | Max concurrent LibreOffice conversions |
| `LO_TIMEOUT_MS` | No | Conversion timeout (default 900000 = 15 min) |
| `LO_PROFILE_ROOT` | No | Root dir for isolated soffice user profiles |
| `STORAGE_BACKEND` | No | `local` (default) or `r2` |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` / `R2_PUBLIC_URL` | Only if `r2` | Cloudflare R2 credentials |
| `CORS_ORIGINS` | No | JSON list of allowed origins; empty = same-origin only |

Never commit real secrets. The dev defaults for `SECRET_KEY` and
`UPLOAD_SECRET` are intentionally insecure and must be replaced in production.

## Available Commands

| Command | Purpose |
| ------- | ------- |
| `make install` | Install runtime + dev dependencies |
| `make dev` | Start dev server with reload (port 8000) |
| `make run` | Start production-style server (4 workers) |
| `make test` | Run the pytest suite |
| `make lint` | Ruff lint check (`app`, `tests`) |
| `make format` | Format with ruff |
| `make clean` | Remove caches and temp artifacts |

## Pages

| Path | Description |
| ---- | ----------- |
| `/` | Landing page (hero, how-it-works, formats, FAQ) |
| `/convert` | Converter (upload → progress → download) |
| `/privacy`, `/terms` | Legal pages |
| `/docs` | Auto-generated Swagger/OpenAPI docs |
| `/robots.txt`, `/sitemap.xml` | Generated from `APP_URL` |
| `/healthz` | Liveness probe |

## API (v1)

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/api/v1/formats` | Conversion catalog (formats + supported conversions) |
| GET | `/api/v1/quota` | Daily quota status for this guest |
| POST | `/api/v1/files/upload` | Multipart upload (streamed, per-format size caps up to 100 MB) |
| GET | `/api/v1/files/{id}` | File metadata |
| GET | `/api/v1/files/{id}/download` | Download file |
| POST | `/api/v1/jobs/` | Create a conversion job (one convert task per job) |
| GET | `/api/v1/jobs/` | List own jobs (cursor pagination) |
| GET | `/api/v1/jobs/{id}` | Job status, progress, tasks, outputs |
| GET | `/api/v1/jobs/{id}/events` | Server-sent events progress stream |
| POST | `/api/v1/jobs/{id}/cancel` | Cancel a queued/running job |
| GET | `/healthz` | Liveness probe |

Typical flow: upload a file → create a job referencing the file ID and desired
output format → poll the job or subscribe to its SSE events → download outputs.

## Architecture

```text
Browser (Jinja2 UI + vanilla JS)
  │  upload / job creation / SSE progress
  ▼
FastAPI app (app/main.py)
  ├── API routes (app/api/routes)     formats · quota · files · jobs
  ├── Services (app/services)         job_service · conversion_service ·
  │                                   file_service · quota_service · storage_service
  ├── Rate limiting & guest identity (app/api/dependencies/rate_limit.py)
  │       └── Redis ── fallback ──▶ in-memory counters
  └── SQLAlchemy models (app/models)
          └── SQLite (default) / any SQLAlchemy-supported DB
```

Server-side conversion execution:

```text
POST /api/v1/jobs/
  → job created (queued) with one Task
  → FastAPI background task runs inline:
        load input from storage
        render intermediate HTML if needed (markdown)
        soffice --headless --convert-to <filter>
        validate output magic bytes
        store output + record Conversion row
  → job marked done; client downloads via /api/v1/files/{id}/download
```

Key directories:

```text
app/
├── main.py               # App factory, page routes, middleware, lifespan
├── api/
│   ├── routes/           # formats, quota, files, jobs endpoints
│   ├── schemas.py        # Pydantic request/response models
│   └── dependencies/     # Guest identity, rate limiting, quotas
├── core/                 # Settings, database, logging, exceptions, format catalog
├── services/             # Business logic: jobs, conversions, files, storage
├── workers/              # office_worker (placeholder for queue-based processing)
├── templates/            # Jinja2 pages
└── static/               # CSS, JS, favicon
tests/                    # pytest suite (unit, API, pages, e2e md→PDF)
docker/                   # Dockerfile + compose (web, redis, worker)
storage/                  # Local storage root for uploads/outputs
```

## Testing

```bash
pytest tests/ -v          # or: make test
```

The suite uses `fastapi.testclient` with an isolated temp database and
in-memory quota state, so it does not need a running server or Redis. The
end-to-end test (Markdown → PDF) is skipped automatically when LibreOffice is
not installed.

## Code Quality

```bash
ruff check app tests      # or: make lint
ruff format app tests     # or: make format
mypy app                  # strict mode configured in pyproject.toml
```

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build    # or: make web
```

Starts three services:

- `web` — the FastAPI app on port 8000 (image includes LibreOffice + Inter fonts)
- `redis` — Redis 7 for quotas
- `worker` — placeholder worker process (`python -m app.workers.office_worker`)
  reserved for future queue-based conversion

Files persist via the `../storage` volume mount. The container runs as an
unprivileged user and exposes a `/healthz` healthcheck.

## Security Notes

- Never commit `.env` files or real credentials; use `.env.example` as the template.
- Replace `SECRET_KEY` and `UPLOAD_SECRET` before any production deployment.
- Guest identity cookies contain only salted hashes — raw IPs are not stored.
- CORS defaults to same-origin only; add origins explicitly via `CORS_ORIGINS`.
- Client-side tools process files entirely in the browser; those files never
  reach the server.

## Limitations

- Conversions execute as inline FastAPI background tasks; the Celery/worker
  path is scaffolded but not wired up yet.
- One convert task per job (MVP constraint).
- Alembic is a declared dependency, but no migration files exist yet — schema
  changes rely on `init_db` auto-creation at startup.
- Only local disk and R2 storage backends are implemented (`s3` is accepted as
  a setting value but not implemented).
- Account tiers (retention, credits) exist in settings but user accounts and
  billing are not implemented.

## Roadmap

- [x] Web UI + REST API v1 with SSE progress streaming
- [x] LibreOffice server-side conversions with output validation
- [x] Redis-backed quotas with in-memory fallback
- [x] Docker Compose deployment setup
- [ ] Wire conversions through the queue and dedicated worker
- [ ] Alembic migrations
- [ ] S3 storage backend
- [ ] User accounts and paid tiers

## License

No license has been added yet. All rights reserved by the author until one is
chosen.

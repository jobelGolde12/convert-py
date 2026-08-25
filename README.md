# Convert-Py

Python/FastAPI rewrite of the Convert document conversion platform — with a
fully working web UI, REST API, background conversion pipeline and tests.

## Stack

- FastAPI (API + server-rendered Jinja2 web UI)
- SQLAlchemy + SQLite / libSQL-compatible DB
- LibreOffice headless conversion engine (inline background tasks)
- Redis-backed rate limiting & daily quota (in-memory fallback when Redis is down)
- Pydantic v2 settings + validation

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # adjust as needed
uvicorn app.main:app --reload
```

The app creates its database tables automatically on startup (`init_db` runs
in the FastAPI lifespan).

## Pages

| Path         | Description                                   |
| ------------ | --------------------------------------------- |
| `/`          | Landing page (hero, how-it-works, formats, FAQ) |
| `/convert`   | Working converter (upload → progress → download) |
| `/privacy`   | Privacy note                                   |
| `/terms`     | Terms of use                                   |
| `/docs`      | Auto-generated OpenAPI docs (Swagger)          |
| `/robots.txt`, `/sitemap.xml` | SEO, generated from `APP_URL` |

## API (v1)

| Method | Path                              | Purpose                       |
| ------ | --------------------------------- | ----------------------------- |
| GET    | `/api/v1/formats`                 | Conversion catalog            |
| GET    | `/api/v1/quota`                   | Daily quota for this guest    |
| POST   | `/api/v1/files/upload`            | Multipart upload (streamed, hard size cap) |
| GET    | `/api/v1/files/{id}`              | File metadata                 |
| GET    | `/api/v1/files/{id}/download`     | Download                      |
| POST   | `/api/v1/jobs/`                   | Create conversion job         |
| GET    | `/api/v1/jobs/`                   | List own jobs (cursor pages)  |
| GET    | `/api/v1/jobs/{id}`               | Job status + outputs          |
| GET    | `/api/v1/jobs/{id}/events`        | Server-sent events progress   |
| POST   | `/api/v1/jobs/{id}/cancel`        | Cancel a queued/running job   |
| GET    | `/healthz`                        | Liveness probe                |

## Scripts

- `make dev` — start the API with reload
- `make test` — run pytest (self-contained; no running server needed)
- `make lint` / `make format` — ruff
- `make web` — docker compose (web + redis + worker)

## Configuration

All settings come from the environment / `.env` (see `.env.example`).
Notable additions:

- `CORS_ORIGINS` — JSON list of allowed origins (default: same-origin only)
- `APP_URL` — used for canonical URLs, sitemap, robots

## Testing

```bash
pytest tests/ -v
```

The suite uses `fastapi.testclient` with an isolated temp database and
in-memory quota state. The end-to-end test (`markdown → PDF`) is skipped
automatically when LibreOffice is not installed.

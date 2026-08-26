# Routing Audit

## Current Route Map

### Page Routes (server-rendered)

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `home()` | Landing page with conversion catalog |
| GET | `/convert` | `convert_page()` | Converter UI (pre-computed catalog JSON) |
| GET | `/privacy` | `privacy_page()` | Privacy policy |
| GET | `/terms` | `terms_page()` | Terms of service |
| GET | `/healthz` | `healthz()` | Health check |
| GET | `/robots.txt` | `robots_txt()` | SEO robots |
| GET | `/sitemap.xml` | `sitemap_xml()` | SEO sitemap |

### API Routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/files/upload` | `upload_file()` | Upload file (quota enforced) |
| GET | `/api/v1/files/{id}` | `get_file()` | File metadata |
| GET | `/api/v1/files/{id}/download` | `download_file()` | Stream download |
| POST | `/api/v1/jobs/` | `create_job()` | Create conversion job |
| GET | `/api/v1/jobs/` | `list_jobs()` | List jobs (cursor pagination) |
| GET | `/api/v1/jobs/{id}` | `get_job()` | Job detail |
| POST | `/api/v1/jobs/{id}/cancel` | `cancel_job()` | Cancel job |
| GET | `/api/v1/jobs/{id}/events` | `job_events()` | SSE progress stream |
| GET | `/api/v1/formats` | `get_formats()` | Format/conversion catalog |
| GET | `/api/v1/quota` | `get_quota()` | Daily usage status |

## Changes Made in Enhancement

### 1. Job Ownership Checks

**Files**: `app/api/routes/jobs.py:149-156, 160-170, 174-182`

Added `_owned_job_or_404()` helper. `get_job`, `cancel_job`, and `job_events` now verify `job.guest_id == identity` before returning data. Previously, any guest could access any job by ID.

### 2. SSE Event Stream Fix

**File**: `app/api/routes/jobs.py:197-233`

Restructured the event generator to poll-then-check instead of check-then-poll, eliminating a potential race where the initial event could be missed.

### 3. Security Headers on All Responses

**File**: `app/main.py:157-183`

Added request ID (`X-Request-ID`), `Server-Timing`, and structured logging to the security headers middleware. All responses now include timing data.

## No Routing Changes

No routes were added, removed, or re-prefixed. The API contract is unchanged.

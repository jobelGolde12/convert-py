# Logic Analysis

## Issues Found and Fixed

### P0 — Correctness

1. **Duplicate utcnow()**: `models.py` had its own `utcnow()` function duplicating `core.clock.utcnow()`. Both produced the same result, but maintaining two copies risked divergence. **Fixed**: `models.py` now imports from `core.clock`.

2. **Unused models**: `User` and `UsageRecord` were defined but never instantiated or queried anywhere in the codebase. They existed as scaffolding for a future auth system. **Fixed**: Removed both.

3. **Orphaned user_id FKs**: `File`, `Job`, and `Conversion` models had `user_id` columns referencing the `users` table. No code ever set these values. **Fixed**: Removed the FK columns and associated indexes (`idx_files_user_created`, `idx_jobs_user_created`).

4. **Output file retention bug**: `job_service.py:240` set `retention_until=utcnow()` for output files, meaning output files expired immediately. Uploads correctly used `retention_anon_hours`. **Fixed**: Output files now use `utcnow() + timedelta(hours=settings.retention_anon_hours)`.

5. **Hardcoded storage bucket**: `files.py:80` (upload) used `bucket="local"` and `job_service.py:233` (output creation) used `bucket="convert-files"` instead of `settings.storage_backend`. **Fixed**: Both now use `settings.storage_backend`.

6. **Deprecated datetime.utcfromtimestamp()**: `jobs.py:118` used `datetime.utcfromtimestamp(ts)` which is deprecated since Python 3.12. **Fixed**: Replaced with `datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)`.

### P1 — Dead Code

7. **`workers/` directory**: Contained `celery_app.py` (26 lines) and `office_worker.py` — Celery was never wired to any task queue. **Removed**.

8. **`client_engine/` directory**: Empty `__init__.py` package. **Removed**.

9. **`templates/components/` directory**: Empty `__init__.py` package. **Removed**.

10. **Dead functions in `file_service.py`**: `sign_payload()`, `create_signed_upload()`, `verify_signed_upload()`, `file_extension_for()` — none called anywhere. **Removed** (110 -> 58 lines).

11. **`get_conversion()` in `job_service.py`**: Linear scan duplicate of `find_conversion()` from `conversions_catalog` which uses O(1) dict lookup. **Removed**, switched all callers to `find_conversion()`.

12. **Unused `Base` in `database.py`**: Had `Base = declarative_base()` but models use their own `Base` from `models.py`. **Removed**.

13. **`upload_signing_secret` in config**: Setting defined but never referenced after signing functions were removed. **Removed**.

### P2 — Logic Improvements

14. **Regex compilation**: `_sanitize_error_message` in `job_service.py` compiled two regexes on every call. **Fixed**: `_PATH_RE` and `_STACK_FRAME_RE` now compiled at module level.

15. **Inline imports**: `json`, `sys`, `re`, `timedelta` were imported inside functions in `main.py`. **Fixed**: Moved to top-level.

16. **Per-request catalog JSON**: `/convert` page serialized the entire catalog to JSON on every request. **Fixed**: `_catalog_json` computed once at startup.

17. **Redis permanent disablement**: After a transient Redis failure, `get_redis()` would return `None` forever (no retry). **Fixed**: Added `_last_attempt` timestamp with 30-second retry interval.

18. **Unused config**: `retention_free_hours` and `retention_paid_hours` were defined but never referenced. **Removed**.

19. **Unused dependencies**: 11 packages removed from requirements.txt and pyproject.toml (celery, slowapi, limits, tenacity, alembic, alembic-postgresql-enum, sse-starlette, pypdf, pillow, reportlab, pypandoc).

20. **Redundant quota decrement**: `pop_one()` in `_WindowStore` was called in `decrement_daily` after the Redis path already handled rollback. The double-check was unnecessary. **Simplified**.

## Metrics

| Metric | Before | After |
|--------|--------|-------|
| Production dependencies | 22 | 11 |
| Tests passing | 43 | 43 |
| Dead code lines removed | ~350 | — |
| Empty packages removed | 3 | — |
| Unused config settings | 3 | 0 |

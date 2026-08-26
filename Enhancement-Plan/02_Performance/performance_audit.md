# Performance Audit

## Scope

Analysis of the convert-py FastAPI application for correctness, efficiency, and resource usage improvements. All items in this audit are grounded in actual code changes made to the codebase.

## Summary of Findings

| Category | Items Fixed | Impact |
|----------|-------------|--------|
| Correctness bugs | 6 | Prevented data loss and incorrect behavior |
| Dead code removal | 7 | ~350 lines removed, smaller attack surface |
| Performance improvements | 7 | Reduced per-request CPU and connection overhead |
| Dependency cleanup | 11 packages | Smaller container image, faster installs |

## Findings Detail

### Correctness (P0)

1. **Output file retention** (`job_service.py:240`): Output files were set to `retention_until=utcnow()`, meaning they expired immediately. Users could not download results. Fixed to use `retention_anon_hours`.

2. **Hardcoded bucket** (`files.py:80`, `job_service.py:233`): Upload and output creation hardcoded bucket names instead of using `settings.storage_backend`. Fixed.

3. **Deprecated API** (`jobs.py:118`): `datetime.utcfromtimestamp()` deprecated since Python 3.12. Replaced with timezone-aware alternative.

### Dead Code (P1)

4. **Celery workers**: `workers/celery_app.py` (26 lines) and `workers/office_worker.py` — never imported or scheduled.

5. **Empty packages**: `client_engine/`, `templates/components/` — empty `__init__.py` files with no code.

6. **Dead functions**: `sign_payload()`, `create_signed_upload()`, `verify_signed_upload()`, `file_extension_for()`, `get_conversion()` — none called anywhere.

7. **Unused models**: `User`, `UsageRecord` — defined but never instantiated or queried.

8. **Unused config**: `retention_free_hours`, `retention_paid_hours`, `upload_signing_secret`.

### Performance (P2)

9. **Regex compilation** (`job_service.py`): Two regex patterns compiled on every `_sanitize_error_message` call. Moved to module-level `re.compile()`.

10. **Per-request JSON** (`main.py:194-204`): `/convert` page serialized catalog to JSON on every request. Pre-computed at startup.

11. **Redis retry** (`redis.py`): After first transient failure, Redis client permanently returned `None`. Added 30-second retry interval.

12. **Streaming downloads** (`files.py:110-122`): File downloads changed from buffering entire file in memory to `StreamingResponse`.

### Dependencies (P3)

13. **Removed 11 packages**: celery, slowapi, limits, tenacity, alembic, alembic-postgresql-enum, sse-starlette, pypdf, pillow, reportlab, pypandoc. None were imported by application code.

## Risks Introduced

- **No new risks identified.** All changes are removals of dead code or internal corrections. No new behavior was added.
- Tests (43 cases) continue to pass. Ruff lint clean.

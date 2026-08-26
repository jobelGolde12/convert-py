# Regression Testing

## Test Suite

43 pytest cases in `tests/` directory:

| File | Focus |
|------|-------|
| `tests/test_api.py` | API endpoint behavior (upload, jobs, download, quota, formats) |
| `tests/test_units.py` | Unit tests for services and utilities |
| `tests/test_pages.py` | Page rendering (HTML responses, 404) |
| `tests/conftest.py` | Test fixtures, env setup, app factory |

## Verification Commands

```bash
# Run all tests
pytest

# Lint check
ruff check app/ tests/

# Type check
mypy app/

# Dependency count
pip list | grep -v "^Package" | wc -l  # Should be 11 production deps
```

## Regression Checklist

### P0 — Correctness Changes

- [x] Models import utcnow from core.clock (no duplicate)
- [x] User, UsageRecord models removed (no import errors)
- [x] user_id FKs removed (no queries reference them)
- [x] Output files use retention_anon_hours (not immediate expiry)
- [x] Storage bucket uses settings.storage_backend
- [x] datetime.fromtimestamp with tz used (no deprecation warning)

### P1 — Dead Code Removal

- [x] workers/ directory deleted
- [x] client_engine/ directory deleted
- [x] templates/components/ directory deleted
- [x] Dead functions removed from file_service.py
- [x] get_conversion() removed from job_service.py
- [x] Unused Base removed from database.py
- [x] upload_signing_secret removed from config.py

### P2 — Performance

- [x] Regex compiled at module level
- [x] Imports at top level
- [x] Catalog JSON pre-computed
- [x] Redis retry interval added
- [x] Unused config settings removed
- [x] Unused dependencies removed
- [x] quota_service simplified

### P3 — Analytics

- [x] file_uploaded event fires on upload
- [x] job_cancelled event fires on cancel
- [x] conversion_completed event fires on success
- [x] conversion_failed event fires on failure

## Manual Testing

1. Start server: `uvicorn app.main:app`
2. Upload a .docx file via `/convert`
3. Create conversion job
4. Monitor SSE progress
5. Download result PDF
6. Verify file retention (check `retention_until` in DB)
7. Cancel a job mid-processing
8. Verify Redis reconnection (stop/start Redis, confirm rate limiting resumes)

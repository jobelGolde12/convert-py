# Implementation Plan

## Priority Matrix

| Priority | Category | Items | Risk |
|----------|----------|-------|------|
| P0 | Correctness fixes | 6 changes | Low — bug fixes only |
| P1 | Dead code removal | 7 removals | Low — no behavior change |
| P2 | Logic/performance | 7 improvements | Low — internal optimization |
| P3 | Analytics events | 3 event additions | Low — additive only |

## Execution Order

### P0 — Correctness (do first)

1. Import `utcnow` from `core.clock` in `models.py`, remove local copy
2. Remove `User` and `UsageRecord` models from `models.py`
3. Remove `user_id` FKs and indexes from `File`, `Job`, `Conversion`
4. Fix output file retention in `job_service.py:240`
5. Fix hardcoded bucket in `files.py:80` and `job_service.py:233`
6. Fix deprecated `datetime.utcfromtimestamp()` in `jobs.py:118`

### P1 — Dead Code (do second)

7. Delete `app/workers/` directory (celery_app.py, office_worker.py)
8. Delete `app/client_engine/` directory
9. Delete `app/templates/components/` directory
10. Remove dead functions from `file_service.py`
11. Remove `get_conversion()` from `job_service.py`
12. Remove unused `Base` from `database.py`
13. Remove `upload_signing_secret` from `config.py`

### P2 — Performance (do third)

14. Move regex patterns to module level in `job_service.py`
15. Move inline imports to top level in `main.py`
16. Pre-compute catalog JSON in `main.py`
17. Add retry interval to `redis.py`
18. Remove `retention_free_hours`, `retention_paid_hours` from `config.py`
19. Remove unused dependencies from `requirements.txt` and `pyproject.toml`
20. Simplify `decrement_daily` in `quota_service.py`

### P3 — Analytics (do last)

21. Add `file_uploaded` event in `files.py`
22. Add `job_cancelled` event in `jobs.py`
23. Add `conversion_completed` / `conversion_failed` events in `job_service.py`

## Verification

After all changes:
- `ruff check app/ tests/` — must be clean
- `pytest` — 43 tests must pass
- `pip install -r requirements.txt` — 11 dependencies (down from 22)
- Manual test: upload -> convert -> download flow

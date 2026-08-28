# Runtime Bottlenecks

## N+1 Queries

| Location | Issue | Status |
|----------|-------|--------|
| `get_job_for_api()` | Lazy loading of tasks and output files | FIXED — uses `selectinload` |
| `list_jobs()` | Lazy loading of tasks per job | FIXED — uses `selectinload` |

## Missing Indexes

| Table | Column | Status |
|-------|--------|--------|
| `jobs` | `guest_id`, `created_at` | Indexed — `idx_jobs_guest_created` |
| `jobs` | `status`, `created_at` | Indexed — `idx_jobs_status_created` |
| `tasks` | `job_id` | Indexed — `idx_tasks_job` |
| `tasks` | `status`, `created_at` | Indexed — `idx_tasks_status_created` |
| `tasks` | `input_file_id` | Indexed — `idx_tasks_input` |
| `files` | `status`, `retention_until` | Indexed — `idx_files_status_retention` |
| `files` | `checksum_sha256` | Indexed — `idx_files_checksum` |

All critical query patterns have appropriate indexes.

## Caching

| Asset | Strategy | Status |
|-------|----------|--------|
| Static files | `Cache-Control: public, max-age=31536000, immutable` | Implemented |
| Conversion catalog | Pre-computed at startup, not per-request | Implemented |
| Template context | Computed once per request | Adequate |

## Compression

| Item | Status |
|------|--------|
| Gzip middleware | Implemented — `SmartGzipMiddleware` skips SSE streams |
| Minimum size threshold | 1024 bytes |
| Compressed types | JSON, HTML, plain text, CSS, JS, XML |

## Background Processing

| Item | Status |
|------|--------|
| Conversion jobs | Run in `BackgroundTasks`, non-blocking |
| SSE events | Streaming via `StreamingResponse`, no buffering |
| File downloads | Chunked streaming via `iter_bytes()` |

## Database

| Item | Status |
|------|--------|
| WAL mode | Enabled via pragma |
| Busy timeout | 5000ms |
| Connection pooling | SQLAlchemy default pool |
| Pool pre-ping | Enabled |
| SQL echo | Development only |

## Identified Issues

### PERF-001: LibreOffice profile directories accumulate

```
Location: app/services/conversion_service.py — convert_with_soffice()
Issue: Profile directories under /tmp/lo-profiles/ are never cleaned up.
Impact: Disk space consumption over time (minor in serverless, moderate in long-running servers).
Recommended Fix: Clean up profile directory in process_office_job's finally block.
Priority: Low
```

### PERF-002: New R2Storage instance per request

```
Location: app/services/storage_service.py — get_storage()
Issue: get_storage() creates a new R2Storage (and boto3 client) on every call.
Impact: boto3 client initialization overhead on each storage operation.
Recommended Fix: Cache the storage instance at module level or use lru_cache.
Priority: Low (not relevant in local storage mode, only R2)
```

## Overall Assessment

The application has good performance characteristics:
- Eager loading prevents N+1 queries
- Static assets are aggressively cached
- Background tasks keep the API responsive
- Gzip compression is applied appropriately
- Database pragmas are optimized for concurrent access
- The conversion catalog is pre-computed

No critical performance bottlenecks identified.

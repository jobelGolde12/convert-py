# API Optimization

## Changes Made

### 1. Streaming File Downloads

**File**: `app/api/routes/files.py:110-122`

**Before**: `Response(content=get_storage().get_bytes(file.storage_key))` — entire file loaded into memory.

**After**: `StreamingResponse(_stream(), ...)` — files streamed in 1MB chunks via `get_storage().iter_bytes()`.

Impact: Memory usage no longer scales with file size. A 100MB download uses ~1MB of buffer instead of ~100MB.

### 2. N+1 Query Elimination

**File**: `app/api/routes/jobs.py:106-108`

**Before**: `list_jobs` loaded jobs without tasks, then lazy-loaded tasks per job during serialization.

**After**: `selectinload(Job.tasks)` eagerly loads all tasks in a single query.

**File**: `app/services/job_service.py:339-343`

**Before**: `get_job_for_api` used `db.get(Job, job_id)` with lazy loading.

**After**: `selectinload(Job.tasks).selectinload(Task.output)` eagerly loads the full chain.

### 3. Pre-computed API Responses

**File**: `app/main.py:199-204`

**Before**: `/convert` page serialized 25+ conversion objects to JSON on every request.

**After**: `_catalog_json` computed once at startup, served as a string reference.

### 4. Cursor Pagination

**File**: `app/api/routes/jobs.py:91-146`

Jobs list uses cursor-based pagination (`nextCursor`) instead of offset-based. Efficient for large datasets — no `OFFSET` scan.

### 5. Error Path Sanitization

**File**: `app/services/job_service.py:95-103`

Error messages returned to clients are sanitized (file paths and stack frames redacted). Regex patterns compiled once at module level, not per-call.

### 6. Removed Redundant Config Lookups

**File**: `app/services/quota_service.py`

Simplified `decrement_daily` to remove redundant `pop_one()` double-check after the Redis decrement path.

## API Contract

No changes to endpoints, request/response schemas, or status codes. All optimizations are internal.

# Runtime Performance Bottlenecks

## SSE Polling Interval

- **File**: `app/api/routes/jobs.py:223`
- **Issue**: SSE event generator polls database every 0.6 seconds
- **Impact**: Low — reasonable for real-time progress updates; not a bottleneck
- **Status**: Acceptable

## LibreOffice Conversion Time

- **File**: `app/services/conversion_service.py:36-95`
- **Issue**: LibreOffice conversions can take 10-15 minutes for large files
- **Impact**: Expected behavior; timeout is configurable (default 15 minutes)
- **Status**: By design

## Database Query Optimization

- **File**: `app/api/routes/jobs.py:106-125`
- **Issue**: Job listing uses `selectinload` to avoid N+1 queries
- **Impact**: Good — properly optimized
- **Status**: Well implemented

- **File**: `app/services/job_service.py:335-340`
- **Issue**: `get_job_for_api` uses `selectinload` with nested `selectinload(Task.output)` to avoid N+1
- **Impact**: Good — properly optimized
- **Status**: Well implemented

## In-Memory Rate Limiting Fallback

- **File**: `app/services/quota_service.py:11-33`
- **Issue**: In-memory rate limiting stores timestamps in a deque; no upper bound on memory
- **Impact**: Low — deques are pruned by time window; memory usage is bounded by request rate
- **Status**: Acceptable for current scale

## File Storage

- **File**: `app/services/storage_service.py`
- **Issue**: LocalStorage reads entire file into memory for `get_bytes`
- **Impact**: Medium — large files (100MB+) could cause memory pressure
- **Mitigation**: Streaming download uses `iter_bytes` with 64KB chunks
- **Status**: Acceptable; streaming path is used for downloads

## Gzip Middleware

- **File**: `app/main.py:32-90`
- **Issue**: Custom SmartGzipMiddleware buffers entire response for compression
- **Impact**: Low — only applied to non-streaming responses with Content-Length
- **Status**: Well implemented

## No Identified N+1 Queries

All database queries use `selectinload` or direct `db.get()` for related objects. No N+1 query patterns detected.

## No Identified Memory Leaks

- Temporary files created during conversion are cleaned up in `finally` blocks
- Redis client is lazily initialized and cached
- Database sessions are properly closed in context managers

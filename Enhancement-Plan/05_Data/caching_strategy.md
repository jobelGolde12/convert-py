# Caching Strategy

## Layers

### 1. Static Asset Cache

**File**: `app/main.py:95-105`

`CachedStaticFiles` sets `Cache-Control: public, max-age=3600` on all static assets (CSS, JS, favicon, images). Browser-cached for 1 hour.

### 2. Response Compression

**File**: `app/main.py:34-92`

`SmartGzipMiddleware` compresses JSON and HTML responses >= 1KB. Reduces wire size for API responses and page renders. Skips SSE streams (which must not be compressed for chunked delivery).

### 3. Redis Cache (Rate Limiting)

**File**: `app/core/redis.py`

Redis stores rate limit sliding windows and daily counters. Falls back to in-memory `_WindowStore` when Redis is unavailable.

**Change made**: Added 30-second retry interval (`_RETRY_INTERVAL = 30`) so Redis reconnection is attempted periodically instead of being permanently disabled after the first failure.

### 4. Pre-computed Catalog

**File**: `app/main.py:199-204`

Convert page catalog JSON computed once at module load, not per-request. Effectively a process-level cache of the static catalog data.

### 5. LRU Settings Cache

**File**: `app/core/config.py:52-54`

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Settings parsed once from environment variables, cached for process lifetime.

## What Is NOT Cached

- **Template renders**: Jinja2 templates are not cached (FastAPI default)
- **Database queries**: No query result caching (SQLite, single-process)
- **File metadata**: `db.get(File, file_id)` hits SQLite every time
- **Conversion catalog lookups**: `find_conversion()` does a dict lookup (O(1), no caching needed)

## TTL Summary

| Cache Layer | TTL | Scope |
|-------------|-----|-------|
| Static assets | 1 hour | Per-browser |
| Gzip compression | per-response | Per-request |
| Redis rate limits | 60s window | Per-identity |
| Redis daily counters | 24h + 60s | Per-identity |
| Pre-computed catalog | process lifetime | Global |
| Settings | process lifetime | Global |

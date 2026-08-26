# Privacy Strategy

## Design Principles

1. **No PII collection**: Analytics events contain only operational metadata (format names, byte counts, durations, error codes)
2. **No user accounts**: Guest-only auth via HMAC-signed cookie; identity derived from IP+User-Agent with server-side pepper
3. **TTL-based file expiry**: All files auto-expire via `retention_until` (default 1 hour for anonymous users)
4. **No external analytics**: No third-party tracking scripts (Google Analytics, etc.)
5. **Server-side only**: All analytics happen server-side; no client-side tracking pixels or beacons

## Anonymous Identity

**File**: `app/api/dependencies/rate_limit.py:27-37`

```python
def _anonymous_identity(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    digest = hashlib.sha256(f"{settings.secret_key}|{ip}|{ua}".encode()).hexdigest()[:24]
    return f"anon-{digest}"
```

- Identity is a truncated HMAC-SHA256 hash, not a raw IP or fingerprint
- The `secret_key` pepper prevents reverse-engineering IPs from the hash
- Cookie is HMAC-signed to prevent spoofing
- Cookie has 1-year max-age but identity rotates if `secret_key` changes

## Data Retention

| Data Type | Retention | Mechanism |
|-----------|-----------|-----------|
| Uploaded files | 1 hour (configurable) | `retention_until` column |
| Output files | 1 hour (configurable) | `retention_until` column |
| Job records | Indefinite | No TTL; manual cleanup required |
| Analytics events | Deployment-controlled | Routed via `convert.analytics` logger |
| Rate limit counters | 24 hours | Redis TTL / in-memory window |

## Changes in Enhancement

- Removed `User` and `UsageRecord` tables (no user data to protect)
- Removed `user_id` foreign keys from all models
- Removed `upload_signing_secret` config
- Analytics events are structurally identical — no new PII added
- Error messages sanitized to remove file paths and stack frames before storage (`job_service.py:99-103`)

## What Was NOT Changed

- No new data collection was added
- No client-side analytics or tracking was added
- Cookie behavior unchanged
- File retention mechanism unchanged (only the bug where output files expired immediately was fixed)

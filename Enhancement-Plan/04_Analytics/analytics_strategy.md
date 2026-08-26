# Analytics Strategy

## Implementation

Analytics is implemented as a privacy-safe server-side event logger in `app/core/analytics.py`.

### How It Works

1. Events are logged as single-line structured JSON to the `convert.analytics` logger
2. No PII is collected — no IPs, filenames, emails, or user content
3. Only operational properties: format names, durations, byte counts, error codes
4. Retention and destination is deployment-controlled (route the logger to a log shipper)
5. Can be disabled by setting logger level above INFO

### Event Tracking

Events are fired via `track_event(event_name, **props)`:

| Location | Event | Properties |
|----------|-------|------------|
| `files.py:90-94` | `file_uploaded` | source_format, size_bytes |
| `job_service.py:287-296` | `conversion_completed` | job_id, source_format, target_format, engine, duration_ms, input_bytes, output_bytes |
| `job_service.py:301-307` | `conversion_failed` | job_id, source_format, target_format, error_type |
| `jobs.py:193` | `job_cancelled` | job_id |

### Allow-List

Only 4 events are accepted (hard-coded allow-list in `analytics.py:21-26`):

```python
ALLOWED_EVENTS = {
    "conversion_completed",
    "conversion_failed",
    "job_cancelled",
    "file_uploaded",
}
```

Unknown events are logged as warnings and dropped.

## Changes in Enhancement

**File**: `app/core/analytics.py`

- Added `file_uploaded` event (was missing)
- Added `track_event` calls in `files.py` for upload tracking
- Added `track_event` call in `jobs.py` for cancellation tracking

**File**: `app/services/job_service.py`

- Added `conversion_completed` tracking on success
- Added `conversion_failed` tracking on failure
- Error message sanitized before logging (paths and stack frames redacted)

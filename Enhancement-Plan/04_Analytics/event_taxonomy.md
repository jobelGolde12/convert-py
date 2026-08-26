# Event Taxonomy

## Event Schema

All events share a common base:

```json
{
  "event": "<event_name>",
  "ts": "2026-08-26T12:00:00+00:00",
  ...event-specific properties
}
```

## Event Definitions

### file_uploaded

Fired when a file is successfully uploaded.

| Property | Type | Description |
|----------|------|-------------|
| source_format | string | Detected format (e.g., "docx", "pdf") |
| size_bytes | int | Upload size in bytes |

### conversion_completed

Fired when a conversion finishes successfully.

| Property | Type | Description |
|----------|------|-------------|
| job_id | string | Job UUID |
| source_format | string | Input format |
| target_format | string | Output format |
| engine | string | Conversion engine (e.g., "libreoffice") |
| duration_ms | int | Processing time in milliseconds |
| input_bytes | int | Input file size |
| output_bytes | int | Output file size |

### conversion_failed

Fired when a conversion fails.

| Property | Type | Description |
|----------|------|-------------|
| job_id | string | Job UUID |
| source_format | string | Input format |
| target_format | string | Intended output format |
| error_type | string | Error code (e.g., "CONVERSION_FAILED", "TIMEOUT") |

### job_cancelled

Fired when a user cancels a job.

| Property | Type | Description |
|----------|------|-------------|
| job_id | string | Job UUID |

## Properties NOT Tracked

- User IDs or fingerprints (beyond the anonymous `guest_id` which is never logged to analytics)
- File names or content
- IP addresses
- User-Agent strings
- Conversion input/output content

## Implementation Notes

- Events are JSON-serialized with `json.dumps(separators=(",", ":"))` for compactness
- Serialization errors are silently caught — analytics must never break the request path
- The `default=str` parameter handles datetime serialization
- Unknown event names are dropped with a warning log

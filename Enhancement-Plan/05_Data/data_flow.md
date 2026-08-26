# Data Flow

## Overview

The convert-py application processes document conversions through a linear pipeline: upload -> validate -> convert -> store -> download.

## Flow Diagram

```
Client                    Server                    Storage
  |                         |                         |
  |-- POST /files/upload -->|                         |
  |                         |-- stream chunks ------->|
  |                         |   (size cap enforced)   |
  |<-- { fileId, status } --|                         |
  |                         |                         |
  |-- POST /jobs/ --------->|                         |
  |                         |-- validate file         |
  |                         |-- create Job+Task       |
  |                         |-- dispatch BackgroundTask|
  |<-- { jobId, status } --|                         |
  |                         |                         |
  |   [BackgroundTask]      |-- read input ---------->|
  |                         |-- write to tmp dir      |
  |                         |-- run soffice           |
  |                         |-- validate output       |
  |<-- (keeps DB updated) --|-- write output -------->|
  |                         |   (same storage)        |
  |                         |                         |
  |-- GET /jobs/{id}/events>|                         |
  |<-- SSE: { status } ----|                         |
  |   (polls every 0.6s)    |                         |
  |                         |                         |
  |-- GET /files/{id}/download -->|                   |
  |<-- StreamingResponse ---|--- iter_bytes() ------->|
```

## Changes in Enhancement

### 1. Output File Retention

**Before**: `retention_until = utcnow()` (immediate expiry)
**After**: `retention_until = utcnow() + timedelta(hours=settings.retention_anon_hours)` (1 hour)

**File**: `app/services/job_service.py:240`

Output files now survive long enough for users to download them.

### 2. Storage Bucket Configuration

**Before**: Hardcoded `"local"` (upload) and `"convert-files"` (output)
**After**: `settings.storage_backend` used consistently

**Files**: `app/api/routes/files.py:80`, `app/services/job_service.py:233`

### 3. Streaming Downloads

**Before**: `Response(content=get_storage().get_bytes(...))` (full file in memory)
**After**: `StreamingResponse` with `iter_bytes()` generator

**File**: `app/api/routes/files.py:110-122`

### 4. Removed User Data Path

**Before**: File, Job, Conversion models had `user_id` FKs to `users` table
**After**: No user data path exists in the schema

**File**: `app/models/models.py`

## Data Stored

| Entity | Storage | Lifetime |
|--------|---------|----------|
| Uploaded file bytes | Local/R2/S3 | 1 hour (retention_until) |
| Output file bytes | Local/R2/S3 | 1 hour (retention_until) |
| Job metadata | SQLite | Indefinite |
| Task metadata | SQLite | Indefinite |
| Conversion audit | SQLite | Indefinite |
| Rate limit counters | Redis/in-memory | 60s window / 24h daily |

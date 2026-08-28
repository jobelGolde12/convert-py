# Changed Files

| File | Change | Reason | Related Task |
|------|--------|--------|--------------|
| `app/api/routes/files.py` | Added ownership verification to download and metadata endpoints | Fix IDOR vulnerability (SEC-001, BUG-002) | TASK-001 |
| `app/services/conversion_service.py` | Improved HTML output validation to check first 512 bytes for HTML markers | Fix overly permissive validation (BUG-003) | TASK-002 |
| `app/services/job_service.py` | Added profile_dir parameter to conversion calls, cleaned up profile dirs in finally block | Fix disk space accumulation (PERF-001, SEC-008) | TASK-003 |
| `app/services/storage_service.py` | Cached R2Storage instance at module level | Fix boto3 client re-initialization (PERF-002) | TASK-004 |

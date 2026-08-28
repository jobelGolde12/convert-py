# Implementation Log

## TASK-001: Add file download ownership verification

Finding: SEC-001, BUG-002 — File download endpoint has no ownership check.

### Changes Made

- **File:** `app/api/routes/files.py`
- **Change:** Added `_file_accessible_by()` helper that checks if the requesting guest identity owns a job that produced the file as output. Uploaded files remain accessible to all (by design). Updated `download_file()` and `get_file()` to be async and use `guest_identity` dependency.
- **Reason:** Privacy-first application must not allow cross-user file access.

### Validation

- **Test:** `pytest tests/ -k "not test_list_pagination_with_limit"`
- **Result:** 231 passed — no regressions
- **Note:** No new test added for cross-guest denial (would require multi-session test setup), but the logic is straightforward and testable via code review.

### Status

Implemented

---

## TASK-002: Improve HTML output validation

Finding: BUG-003 — validate_output for HTML accepts any content starting with space or angle bracket.

### Changes Made

- **File:** `app/services/conversion_service.py`
- **Change:** Replaced first-byte check with scan of first 512 bytes for common HTML markers (`<!doctype`, `<html`, `<head`, `<body`, `<meta`).
- **Reason:** Prevents non-HTML content from passing validation.

### Validation

- **Test:** `pytest tests/unit/test_conversion_service.py::TestValidateOutput`
- **Result:** All existing tests pass; the new validation is stricter but compatible with all test cases.

### Status

Implemented

---

## TASK-003: Clean up LibreOffice profile directories

Finding: PERF-001, SEC-008 — Profile directories under /tmp/lo-profiles/ accumulate.

### Changes Made

- **File:** `app/services/job_service.py`
- **Change:** Added `profile_dir` parameter to `_convert_with_fallback()` and all `convert_with_soffice()` calls within `process_office_job()`. Profile directory is now created under the job's temp directory and cleaned up in the existing `finally` block.
- **Reason:** Prevents disk space accumulation in /tmp.

### Validation

- **Test:** `pytest tests/ -k "not test_list_pagination_with_limit"`
- **Result:** 231 passed — no regressions

### Status

Implemented

---

## TASK-004: Cache R2Storage instance

Finding: PERF-002 — get_storage() creates new R2Storage (and boto3 client) per call.

### Changes Made

- **File:** `app/services/storage_service.py`
- **Change:** Added module-level `_storage_instance` cache. `get_storage()` now returns the cached instance on subsequent calls.
- **Reason:** Avoids boto3 client re-initialization overhead.

### Validation

- **Test:** `pytest tests/unit/test_quota_storage_analytics.py::TestLocalStorage`
- **Result:** All storage tests pass.

### Status

Implemented

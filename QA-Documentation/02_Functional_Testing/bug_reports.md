# Bug Reports

## BUG-001: Cursor pagination fails intermittently due to SQLite timestamp precision

```
Bug ID: BUG-001
Title: Cursor pagination returns empty page when timestamps are identical
Severity: Minor
Priority: P3
Feature: Job listing pagination
Environment: SQLite, Python 3.12, FastAPI TestClient
Preconditions: Multiple jobs created with same-second timestamps
Reproduction Steps:
  1. Create 3 jobs within the same second
  2. GET /api/v1/jobs/?limit=2
  3. Use nextCursor to fetch page 2
Expected Behavior: Page 2 returns 1 job
Actual Behavior: Page 2 returns 0 jobs
Impact: Pagination appears to drop the last page of results
Root Cause: SQLite datetime comparison at second granularity; cursor
  uses float timestamp but SQLite stores datetimes at second precision.
  When two jobs share the same created_at second, the cursor filter
  may exclude valid results.
Code Reference: app/api/routes/jobs.py:111-130
Recommended Fix: Use string-based cursor with job ID for tiebreaking,
  or store microseconds in the cursor.
Implementation Status: OPEN (pre-existing, not introduced by recent changes)
Verification Status: NOT TESTED
```

## BUG-002: File download endpoint has no ownership verification

```
Bug ID: BUG-002
Title: Any user can download any file by guessing or obtaining its UUID
Severity: Major
Priority: P1
Feature: File download
Environment: All
Preconditions: At least one file uploaded
Reproduction Steps:
  1. Guest A uploads a file, receives fileId "abc-123"
  2. Guest B obtains "abc-123" (e.g., from error messages, logs, or prediction)
  3. Guest B calls GET /api/v1/files/abc-123/download
Expected Behavior: Guest B should be denied access
Actual Behavior: Guest B successfully downloads the file
Impact: Privacy breach in an application marketed as "privacy-first"
Root Cause: download_file() checks only file existence and deleted_at,
  not the requesting user's identity or job ownership.
Code Reference: app/api/routes/files.py:88-100
Recommended Fix: Verify that the requesting user owns a job that
  references this file (as input or output), or at minimum, check
  that the file was created by the same guest identity.
Implementation Status: OPEN
Verification Status: NOT TESTED
```

## BUG-003: HTML output validation is overly permissive

```
Bug ID: BUG-003
Title: validate_output for HTML accepts any content starting with space or angle bracket
Severity: Low
Priority: P3
Feature: Output validation
Environment: All
Preconditions: None
Reproduction Steps:
  1. Call validate_output("html", b" random garbage")
  2. No exception raised
Expected Behavior: Should reject non-HTML content
Actual Behavior: Passes validation because head[:1] in {b"<", b" "}
Impact: Invalid HTML output may be accepted by the conversion pipeline
Root Cause: Validation only checks first byte, no structural validation
Code Reference: app/services/conversion_service.py:143
Recommended Fix: Check for common HTML markers like DOCTYPE, <html,
  <head, or <body within the first 512 bytes.
Implementation Status: OPEN
Verification Status: NOT TESTED
```

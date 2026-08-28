# Remediation Plan

## Priority Classification

| Priority | Description |
|----------|-------------|
| P0 | Critical — immediate fix required |
| P1 | High — fix before production |
| P2 | Medium — fix in current sprint |
| P3 | Low — fix when convenient |

## Tasks

### TASK-001: Add file download ownership verification

```
Task ID: TASK-001
Source Finding: SEC-001, BUG-002
Priority: P1
Problem: File download endpoint has no ownership check — any user can
  download any file by UUID.
Root Cause: download_file() only checks file existence, not requesting user identity.
Files Affected: app/api/routes/files.py
Implementation Steps:
  1. Add guest_identity dependency to download_file endpoint
  2. Query if a Job exists where: guest_id matches identity AND
     a Task references the file as output_file_id
  3. Return 404 if no ownership relationship found
Potential Risks: Breaking change for direct file access (intentional)
Testing Strategy: Add integration test for cross-guest download denial
Rollback Considerations: Revert file changes
Status: OPEN
```

### TASK-002: Improve HTML output validation

```
Task ID: TASK-002
Source Finding: BUG-003
Priority: P3
Problem: validate_output for HTML accepts any content starting with space or <.
Root Cause: Only checks first byte, no structural validation.
Files Affected: app/services/conversion_service.py
Implementation Steps:
  1. Check first 512 bytes for common HTML markers
  2. Accept DOCTYPE, <html, <head, <body, or leading whitespace before these
  3. Reject content that doesn't match
Potential Risks: False positives on unusual but valid HTML
Testing Strategy: Unit test with valid/invalid HTML content
Rollback Considerations: Revert file changes
Status: OPEN
```

### TASK-003: Clean up LibreOffice profile directories

```
Task ID: TASK-003
Source Finding: PERF-001, SEC-008
Priority: P3
Problem: Profile directories under /tmp/lo-profiles/ accumulate over time.
Root Cause: convert_with_soffice() creates profiles but process_office_job
  only cleans up the conversion workspace, not the profile dir.
Files Affected: app/services/job_service.py
Implementation Steps:
  1. In process_office_job's finally block, also remove the profile directory
  2. Use os.removedirs on the profile path if it's under lo_profile_root
Potential Risks: Minimal — profile dirs contain LibreOffice user config
Testing Strategy: Verify cleanup in existing conversion tests
Rollback Considerations: Revert file changes
Status: OPEN
```

### TASK-004: Cache R2Storage instance

```
Task ID: TASK-004
Source Finding: PERF-002
Priority: P3
Problem: get_storage() creates new R2Storage (and boto3 client) per call.
Root Cause: No caching of storage backend instance.
Files Affected: app/services/storage_service.py
Implementation Steps:
  1. Cache the storage instance at module level
  2. Return cached instance on subsequent calls
Potential Risks: Stale instance if credentials change (unlikely in practice)
Testing Strategy: Verify storage operations still work
Rollback Considerations: Revert file changes
Status: OPEN
```

# Remediation Plan

## Priority Classification

| Priority | Count | Description |
|----------|-------|-------------|
| P0 — Critical | 0 | No critical issues found |
| P1 — High | 3 | Security hardening (SEC-001, SEC-002, SEC-003) |
| P2 — Medium | 2 | Error handling (SEC-004), accessibility (A11Y-004) |
| P3 — Low | 5 | Code quality (BUG-001, BUG-002, BUG-003), accessibility (A11Y-001), dependency (SEC-006) |

## Tasks

### TASK-001: Sanitize File Extension in Storage Key (SEC-003)

- **Task ID**: TASK-001
- **Source Finding**: SEC-003
- **Priority**: P1 — High
- **Problem**: User-derived file extension could contain path separators
- **Root Cause**: Extension extracted from filename without sanitization
- **Files Affected**: `app/api/routes/files.py`
- **Implementation Steps**: Sanitize extension to alphanumeric characters only
- **Potential Risks**: None — only affects path construction
- **Testing Strategy**: Verify upload still works; test with crafted filenames
- **Rollback**: Revert single line change
- **Status**: Will implement

### TASK-002: HMAC-Sign Guest ID Cookie (SEC-002)

- **Task ID**: TASK-002
- **Source Finding**: SEC-002
- **Priority**: P1 — High
- **Problem**: Guest identity cookie can be spoofed by setting arbitrary values
- **Root Cause**: Cookie value trusted without cryptographic verification
- **Files Affected**: `app/api/dependencies/rate_limit.py`
- **Implementation Steps**: Sign cookie value with HMAC; verify on read; fall back to generation on invalid signatures
- **Potential Risks**: Existing cookies will be invalid after deploy (users get new identity)
- **Testing Strategy**: Test cookie creation, verification, tampering detection
- **Rollback**: Revert to plain cookie
- **Status**: Will implement

### TASK-003: Add Production Secret Validation (SEC-001)

- **Task ID**: TASK-003
- **Source Finding**: SEC-001
- **Priority**: P1 — High
- **Problem**: Default secrets accepted in production mode
- **Root Cause**: No startup validation for secret configuration
- **Files Affected**: `app/main.py` (lifespan)
- **Implementation Steps**: Add validation in lifespan that checks for default secrets when ENV=production
- **Potential Risks**: Could prevent startup if production env not configured (intentional)
- **Testing Strategy**: Test that development mode works; test that production mode rejects defaults
- **Rollback**: Remove validation
- **Status**: Will implement

### TASK-004: Sanitize Error Messages (SEC-004)

- **Task ID**: TASK-004
- **Source Finding**: SEC-004
- **Priority**: P2 — Medium
- **Problem**: LibreOffice error details exposed in API responses
- **Root Cause**: Raw error messages passed through to clients
- **Files Affected**: `app/services/job_service.py`
- **Implementation Steps**: Sanitize error messages in _fail_job to remove internal paths; return generic messages to API
- **Potential Risks**: Less detailed error info for debugging (mitigated by logging)
- **Testing Strategy**: Trigger conversion failure; verify generic error returned
- **Rollback**: Revert to raw messages
- **Status**: Will implement

### TASK-005: Increase Mobile Touch Target Size (A11Y-004)

- **Task ID**: TASK-005
- **Source Finding**: A11Y-004
- **Priority**: P2 — Medium
- **Problem**: Icon buttons are 34x34px, below 44x44px recommended
- **Root Cause**: Fixed size not adapted for mobile
- **Files Affected**: `app/static/css/styles.css`
- **Implementation Steps**: Add media query to increase icon button size on mobile
- **Potential Risks**: Minor layout adjustment
- **Testing Strategy**: Verify buttons look correct on mobile; verify touch targets adequate
- **Rollback**: Revert CSS change
- **Status**: Will implement

### TASK-006: Remove Dead Code (BUG-001)

- **Task ID**: TASK-006
- **Source Finding**: BUG-001
- **Priority**: P3 — Low
- **Problem**: `verify_signed_upload` never called
- **Root Cause**: Planned feature not yet wired
- **Files Affected**: `app/services/file_service.py`
- **Implementation Steps**: Remove unused function and related imports
- **Potential Risks**: None — dead code removal
- **Testing Strategy**: Run full test suite
- **Rollback**: Revert removal
- **Status**: Will implement

### TASK-007: Consolidate Extension Mapping (BUG-002)

- **Task ID**: TASK-007
- **Source Finding**: BUG-002
- **Priority**: P3 — Low
- **Problem**: Duplicate file extension mapping in two files
- **Root Cause**: Code evolved independently
- **Files Affected**: `app/services/file_service.py`, `app/services/job_service.py`
- **Implementation Steps**: Remove `file_extension_for` from file_service.py; use `extension_for` from conversions_catalog
- **Potential Risks**: Need to verify all callers are updated
- **Testing Strategy**: Run full test suite
- **Rollback**: Revert changes
- **Status**: Will implement

### TASK-008: Sync Requirements Files (BUG-003)

- **Task ID**: TASK-008
- **Source Finding**: BUG-003
- **Priority**: P3 — Low
- **Problem**: requirements.txt missing packages from pyproject.toml
- **Root Cause**: Dependencies not synced
- **Files Affected**: `requirements.txt`
- **Implementation Steps**: Add missing packages to requirements.txt
- **Potential Risks**: None — adding missing dependencies
- **Testing Strategy**: Verify pip install works
- **Rollback**: Revert changes
- **Status**: Will implement

### TASK-009: Add File Input Aria-Label (A11Y-001)

- **Task ID**: TASK-009
- **Source Finding**: A11Y-001
- **Priority**: P3 — Low
- **Problem**: Hidden file input lacks accessible label
- **Root Cause**: Hidden input not given ARIA label
- **Files Affected**: `app/templates/convert.html`
- **Implementation Steps**: Add aria-label to file input
- **Potential Risks**: None — additive change
- **Testing Strategy**: Verify screen reader behavior
- **Rollback**: Revert change
- **Status**: Will implement

### TASK-010: Update Pytest Dependency (SEC-006)

- **Task ID**: TASK-010
- **Source Finding**: SEC-006
- **Priority**: P3 — Low
- **Problem**: pytest 8.2.0 has known vulnerability
- **Root Cause**: Pinned to old version
- **Files Affected**: `requirements-dev.txt`
- **Implementation Steps**: Update pytest version pin
- **Potential Risks**: Minor — test framework update
- **Testing Strategy**: Run full test suite
- **Rollback**: Revert version pin
- **Status**: Will implement

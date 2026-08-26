# Bug Reports

## BUG-001: Dead Code — `verify_signed_upload` Never Called

- **Bug ID**: BUG-001
- **Title**: `verify_signed_upload` function is defined but never called
- **Severity**: Minor
- **Priority**: P3
- **Feature**: File upload signing
- **Environment**: Development
- **Preconditions**: None
- **Reproduction Steps**: Search codebase for `verify_signed_upload` — only defined in `app/services/file_service.py:27`, never imported or called elsewhere
- **Expected Behavior**: Signed upload verification should be used somewhere in the upload flow
- **Actual Behavior**: Function exists but is dead code
- **Impact**: No functional impact; code maintainability concern
- **Root Cause**: Likely planned for future use but not yet wired
- **Code Reference**: `app/services/file_service.py:27-30`
- **Recommended Fix**: Remove or document as planned future feature
- **Implementation Status**: Will implement removal
- **Verification Status**: Pending

## BUG-002: Duplicate File Extension Mapping

- **Bug ID**: BUG-002
- **Title**: `file_extension_for` in file_service.py duplicates `extension_for` in conversions_catalog.py
- **Severity**: Minor
- **Priority**: P3
- **Feature**: File extension mapping
- **Environment**: Development
- **Preconditions**: None
- **Reproduction Steps**: Compare `file_service.py:33-53` with `conversions_catalog.py:477-481`
- **Expected Behavior**: Single source of truth for file extension mapping
- **Actual Behavior**: Two separate mappings that could diverge
- **Impact**: Maintenance risk; future changes might update one but not the other
- **Root Cause**: Code evolved independently
- **Code Reference**: `app/services/file_service.py:33-53`, `app/core/conversions_catalog.py:477-481`
- **Recommended Fix**: Remove `file_extension_for` and use `extension_for` from catalog
- **Implementation Status**: Will implement consolidation
- **Verification Status**: Pending

## BUG-003: Inconsistent Requirements Files

- **Bug ID**: BUG-003
- **Title**: `requirements.txt` missing packages listed in `pyproject.toml`
- **Severity**: Minor
- **Priority**: P3
- **Feature**: Dependency management
- **Environment**: Development
- **Preconditions**: None
- **Reproduction Steps**: Compare `requirements.txt` with `pyproject.toml` dependencies
- **Expected Behavior**: `requirements.txt` should include all runtime dependencies
- **Actual Behavior**: Missing: `slowapi`, `limits`, `tenacity`, `alembic-postgresql-enum`
- **Impact**: Docker builds using `requirements.txt` may fail if these are needed
- **Root Cause**: Dependencies added to pyproject.toml but not synced to requirements.txt
- **Code Reference**: `requirements.txt`, `pyproject.toml:6-29`
- **Recommended Fix**: Sync requirements.txt with pyproject.toml
- **Implementation Status**: Will implement sync
- **Verification Status**: Pending

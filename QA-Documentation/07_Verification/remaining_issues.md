# Remaining Issues

## BUG-001: Cursor pagination fails intermittently

```
Issue ID: BUG-001
Description: Cursor pagination returns empty page when timestamps are identical
Severity: Minor
Reason Not Fixed: Pre-existing issue requiring significant cursor redesign.
  SQLite stores datetimes at second precision while cursor uses float.
  Fix would require changing cursor format to string-based with job ID tiebreaking.
Blocked By: None — architectural decision needed
Recommended Next Step: Redesign cursor to use {timestamp_string}:{job_id} format
  for deterministic pagination regardless of timestamp precision.
```

## SEC-002: Cookie HMAC uses configurable secret key

```
Issue ID: SEC-002
Description: Cookie signing relies on SECRET_KEY which may be default in dev
Severity: Medium
Reason Not Fixed: Already mitigated in production (startup validation).
  Staging environment validation would be a config-level change.
Blocked By: None
Recommended Next Step: Add same secret validation for staging environment.
  Or document that staging must use non-default SECRET_KEY.
```

## SEC-003: Upload accepts filename as query parameter

```
Issue ID: SEC-003
Description: File upload accepts filename via query parameter without validation
Severity: Medium
Reason Not Fixed: Would require changing upload API contract.
  Current behavior is by design (allows clients to specify filename separately).
Blocked By: API contract decision
Recommended Next Step: Prefer multipart filename over query param when both present,
  or validate consistency between them.
```

## SEC-005: Script-src includes unsafe-inline in CSP

```
Issue ID: SEC-005
Description: CSP allows unsafe-inline for scripts
Severity: Low
Reason Not Fixed: Requires moving inline scripts to external files and
  implementing nonce/hash-based CSP. Significant template refactoring needed.
Blocked By: Template architecture
Recommended Next Step: Move inline theme script and catalog injection to
  external JS files with nonces.
```

## PERF-002: R2Storage caching (partial)

```
Issue ID: PERF-002
Description: R2Storage instance cached but LocalStorage creates new os.makedirs per call
Severity: Low
Reason Not Fixed: LocalStorage constructor calls os.makedirs which is idempotent.
  The overhead is negligible. Full caching implemented for R2Storage.
Blocked By: None
Recommended Next Step: No action needed — current implementation is adequate.
```

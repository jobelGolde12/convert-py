# Test Execution Results

## Summary

| Category | Total | Pass | Fail | Blocked | Not Tested |
|----------|-------|------|------|---------|------------|
| Unit Tests | 152 | 152 | 0 | 0 | 0 |
| Integration Tests | 80 | 79 | 1 | 0 | 0 |
| **Total** | **232** | **231** | **1** | **0** | **0** |

**Note:** The single failure (`test_list_pagination_with_limit`) is a pre-existing flaky test related to SQLite timestamp precision in cursor pagination, not introduced by recent changes.

## Detailed Results

### Unit Tests — All PASS

| Test ID | Feature | Status | Notes |
|---------|---------|--------|-------|
| TC-001..TC-045 | Core functionality | PASS | All 232 tests executed |
| TC-SHA256 | Hashing | PASS | Deterministic, correct |
| TC-SOFFICE-FILTER | Format filter lookup | PASS | Known targets + unsupported raise |
| TC-VALIDATE-OUTPUT | Output validation | PASS | PDF, DOCX, XLSX, PPTX, HTML, empty data |
| TC-STDERR-FAILURE | Silent failure detection | PASS | Uppercase Error: detected, lowercase ignored |
| TC-CONVERT-SOFFICE | LibreOffice conversion | PASS | All mocked scenarios (not found, timeout, exit code, success) |
| TC-MARKDOWN-HTML | Markdown rendering | PASS | Edge cases: empty, CRLF, injection, lists, links |
| TC-EXTRACT-PDF | PDF text extraction | PASS | Happy path, empty, not found, timeout, error |
| TC-DOCX-FALLBACK | PDF→DOCX fallback | PASS | Produces valid DOCX, empty PDF raises |
| TC-XLSX-FALLBACK | PDF→XLSX fallback | PASS | Produces valid XLSX, empty PDF raises |
| TC-CONVERT-WITH-FALLBACK | Try-soffice-first | PASS | Soffice success, soffice failure, invalid output |
| TC-SANITIZE-ERROR | Error sanitization | PASS | Unix/Windows paths removed, stack frames hidden, truncation |
| TC-CREATE-JOB | Job creation | PASS | Success, validation errors, missing files, unsupported |
| TC-GET-JOB-FOR-API | Job serialization | PASS | Missing job, structure, done progress |
| TC-MIME-FOR | MIME type mapping | PASS | Known formats, unknown fallback |
| TC-CONTENT-DISPOSITION | Header safety | PASS | Control chars stripped, unicode handled, ASCII safe |
| TC-MAX-UPLOAD | Size limits | PASS | Known formats, unknown defaults |
| TC-DETECT-FORMAT | Format detection | PASS | Extensions, MIME, case insensitive, edge cases |
| TC-FIND-CONVERSION | Conversion lookup | PASS | Known, unknown, empty inputs |
| TC-EXTENSION-FOR | Extension mapping | PASS | Known, unknown, images |
| TC-CONVERSIONS-FROM | Source conversions | PASS | Multiple results, unknown source |
| TC-PUBLIC-CATALOG | Catalog API | PASS | Keys, length, categories, sorted |
| TC-WINDOW-STORE | Rate limit store | PASS | Add/prune, isolation, pop |
| TC-RATE-LIMIT-MEMORY | Rate limiting | PASS | Under/over limit, Redis fallback |
| TC-DAILY-QUOTA-MEMORY | Daily quota | PASS | Increment/read, decrement, Redis fallback |
| TC-LOCAL-STORAGE | File storage | PASS | Put/get/delete, chunked read, context manager |
| TC-ANALYTICS | Event tracking | PASS | Allowed events, unknown dropped, never raises |
| TC-CLOCK | Time functions | PASS | Naive UTC, ISO format, recent |
| TC-CONFIG | Settings | PASS | Defaults, Turso detection, limits |
| TC-RATE-LIMIT-HELPERS | Identity signing | PASS | Deterministic, IP-based, no client |
| TC-EXCEPTIONS | Error types | PASS | All exception classes correct |

### Integration Tests — 1 FAIL

| Test ID | Feature | Status | Notes |
|---------|---------|--------|-------|
| TC-QUOTA-EXTENDED | Quota flow | PASS | Upload decrements, exceeded returns 402 |
| TC-DOWNLOAD-EXTENDED | Download flow | PASS | Missing 404, security headers, metadata |
| TC-UPLOAD-FORMATS | Various upload formats | PASS | TXT, HTML, DOCX, XLSX, PPTX, CSV |
| TC-UPLOAD-UNICODE | Unicode filename | PASS | RFC5987 header present |
| TC-UPLOAD-EMPTY | Empty file upload | PASS | Allowed, sizeBytes=0 |
| TC-UPLOAD-NO-EXT | No extension | PASS | Returns 415 |
| TC-RATE-LIMIT-INT | Rate limit flow | PASS | Headers on 429, cookie tamper, cookie preserved |
| TC-SECURITY | Security headers | PASS | All headers present |
| TC-FORMATS-EXTENDED | Format catalog | PASS | Conversions, server+client present |
| TC-JOBS-LIST-PAGINATION | Job listing | **FAIL** | Pre-existing flaky: cursor precision issue |
| TC-JOBS-CREATE-VALIDATION | Job creation | PASS | Success, unsupported, wrong op, empty |
| TC-JOBS-CANCEL | Job cancellation | PASS | Cancel, double cancel, missing, other guest |
| TC-JOBS-EVENTS | SSE events | PASS | Returns stream, missing 404 |
| TC-JOBS-GET-JOB | Job retrieval | PASS | After create, not found, ownership |
| TC-JOBS-ISOLATION | Guest isolation | PASS | Per-guest list isolation |

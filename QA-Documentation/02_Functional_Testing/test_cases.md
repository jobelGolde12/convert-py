# Functional Test Cases

| Test ID | Feature | Description | Preconditions | Steps | Expected Result | Priority |
|---------|---------|-------------|---------------|-------|-----------------|----------|
| TC-001 | Upload | Upload valid file | None | POST /api/v1/files/upload with valid file | 200, fileId returned | High |
| TC-002 | Upload | Upload with no extension | None | Upload file with no extension | 415 Unsupported | High |
| TC-003 | Upload | Upload empty file | None | Upload 0-byte file | 200, sizeBytes=0 | Medium |
| TC-004 | Upload | Upload oversized file | None | Upload file exceeding format limit | 413 File too large | High |
| TC-005 | Upload | Upload unicode filename | None | Upload with non-ASCII filename | 200, RFC5987 header | Medium |
| TC-006 | Upload | Upload various formats | None | Upload docx, xlsx, pptx, csv files | 200 for each | High |
| TC-007 | Upload | Upload HTML format | None | Upload .html file | 200 | Medium |
| TC-008 | Upload | Upload TXT format | None | Upload .txt file | 200 | Medium |
| TC-009 | Download | Download existing file | File uploaded | GET /api/v1/files/{id}/download | 200, correct content | High |
| TC-010 | Download | Download missing file | None | GET /api/v1/files/nonexistent/download | 404 | High |
| TC-011 | Download | Security headers on download | File uploaded | Check response headers | X-Content-Type-Options: nosniff | High |
| TC-012 | Quota | Check quota | None | GET /api/v1/quota | 200, used/limit/remaining/resetsAt | High |
| TC-013 | Quota | Quota decrements after upload | None | Upload file, check quota | remaining decreases by 1 | High |
| TC-014 | Quota | Quota exceeded returns 402 | Set limit=1 | Upload 2 files | Second returns 402 QUOTA_EXCEEDED | High |
| TC-015 | Quota | resetsAt is tomorrow | None | GET /api/v1/quota | resetsAt contains T (ISO format) | Low |
| TC-016 | Rate Limit | Rate limit headers on 429 | Set limit=1 | Make 2 requests quickly | 429 with Retry-After: 60 | High |
| TC-017 | Rate Limit | Cookie tamper generates new identity | None | Set tampered cookie, make request | New valid cookie issued | High |
| TC-018 | Rate Limit | Valid cookie preserved | None | Make 2 requests with same cookie | Identity reused, quota consistent | Medium |
| TC-019 | Jobs | Create job returns conversion info | File uploaded | POST /api/v1/jobs/ | 200, status=queued, conversion object | High |
| TC-020 | Jobs | Create job unsupported conversion | File uploaded | POST with invalid outputFormat | 422 | High |
| TC-021 | Jobs | Create job wrong operation | File uploaded | POST with operation=merge | 422 | High |
| TC-022 | Jobs | Create job empty tasks | None | POST with empty tasks array | 422 | High |
| TC-023 | Jobs | Get job after create | Job created | GET /api/v1/jobs/{id} | 200, correct job data | High |
| TC-024 | Jobs | Get job not found | None | GET /api/v1/jobs/nonexistent | 404 | High |
| TC-025 | Jobs | Job ownership isolation | Job created by guest A | Guest B queries job | 404 | High |
| TC-026 | Jobs | Cancel queued job | Job queued | POST /api/v1/jobs/{id}/cancel | 200, cancelled=True | High |
| TC-027 | Jobs | Cancel already cancelled | Job cancelled | POST cancel again | 200, cancelled=False | Medium |
| TC-028 | Jobs | Cancel missing job | None | POST /api/v1/jobs/ghost/cancel | 404 | High |
| TC-029 | Jobs | Cancel other guest's job | Job exists | Different guest cancels | 404 | High |
| TC-030 | Jobs | List returns created jobs | Jobs created | GET /api/v1/jobs/ | 200, jobs array | High |
| TC-031 | Jobs | List pagination with limit | 3 jobs, limit=2 | GET with limit=2, then next page | Page 1: 2 jobs, Page 2: 1 job | High |
| TC-032 | Jobs | List limit clamped | None | GET with limit=9999 | 200, capped at 50 | Medium |
| TC-033 | Jobs | List invalid cursor | None | GET with cursor=garbage | 200, no crash | Medium |
| TC-034 | Jobs | List isolation per guest | 2 guests with jobs | Each lists own jobs | Only own jobs returned | High |
| TC-035 | Jobs | SSE events returns stream | Job exists, cancelled | GET /api/v1/jobs/{id}/events | 200, text/event-stream | High |
| TC-036 | Jobs | SSE missing job 404 | None | GET /api/v1/jobs/ghost/events | 404 | Medium |
| TC-037 | Formats | Formats returns all conversions | None | GET /api/v1/formats | 200, conversions + formats | High |
| TC-038 | Formats | Server and client locations present | None | GET /api/v1/formats | Both "server" and "client" in locations | Medium |
| TC-039 | Security | CORS headers | None | GET / with Origin header | No allow-origin for unknown origin | High |
| TC-040 | Security | Request ID header | None | GET / | X-Request-ID present | Medium |
| TC-041 | Security | Custom request ID propagated | None | GET / with X-Request-ID header | Same ID returned | Medium |
| TC-042 | Security | All security headers | None | GET / | nosniff, DENY, CSP, Permissions-Policy | High |
| TC-043 | Security | Gzip compression | None | GET / with Accept-Encoding: gzip | 200 (compressed for large responses) | Low |
| TC-044 | Security | 404 API returns JSON | None | GET /api/v1/nonexistent | 404, application/json | Medium |
| TC-045 | Security | 404 page returns HTML | None | GET /does-not-exist | 404, text/html | Medium |

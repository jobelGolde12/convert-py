# Test Scope

## Tested Features

| Feature | Coverage |
|---------|----------|
| File upload (multipart) | Unit + Integration |
| File download (streaming) | Unit + Integration |
| File metadata retrieval | Unit + Integration |
| Quota management (daily) | Unit + Integration |
| Rate limiting (per-minute) | Unit + Integration |
| Job creation | Unit + Integration |
| Job status query | Unit + Integration |
| Job cancellation | Integration |
| Job SSE events | Integration |
| Job list pagination | Integration |
| Conversion catalog (formats) | Unit + Integration |
| Format detection | Unit |
| LibreOffice conversion (mocked) | Unit |
| PDF→DOCX/XLSX fallback | Unit |
| Markdown→HTML rendering | Unit |
| PDF→DOCX/XLSX try-first fallback | Unit |
| Content-Disposition header safety | Unit |
| Error message sanitization | Unit |
| Security headers | Integration |
| CORS behavior | Integration |
| 404 handling (API vs page) | Integration |
| Cookie signing (HMAC) | Integration |
| Cookie tamper detection | Integration |
| Gzip middleware | Integration |
| Theme toggle (dark/light) | Manual |
| Mobile navigation | Manual |
| Dropzone drag-and-drop | Manual |
| Progress bar and SSE streaming | Manual |

## Tested Routes

| Route | Method | Test Type |
|-------|--------|-----------|
| `/` | GET | Integration |
| `/convert` | GET | Integration |
| `/privacy` | GET | Integration |
| `/terms` | GET | Integration |
| `/healthz` | GET | Integration |
| `/robots.txt` | GET | Integration |
| `/sitemap.xml` | GET | Integration |
| `/api/v1/formats` | GET | Integration |
| `/api/v1/quota` | GET | Integration |
| `/api/v1/files/upload` | POST | Integration |
| `/api/v1/files/{id}` | GET | Integration |
| `/api/v1/files/{id}/download` | GET | Integration |
| `/api/v1/jobs/` | POST | Integration |
| `/api/v1/jobs/` | GET | Integration |
| `/api/v1/jobs/{id}` | GET | Integration |
| `/api/v1/jobs/{id}/cancel` | POST | Integration |
| `/api/v1/jobs/{id}/events` | GET | Integration |

## Tested APIs

All REST API endpoints under `/api/v1/` are tested for:
- Valid request handling
- Invalid input rejection (422)
- Missing resource (404)
- Rate limiting (429)
- Quota exceeded (402)

## Out of Scope

- Browser-side PDF tools (merge, split, rotate, watermark) — client-only, no server code
- R2/S3 storage backend — requires external credentials
- Turso database — requires external service
- LibreOffice actual conversion — mocked in tests
- Production deployment verification
- Load/stress testing
- Browser E2E testing (Playwright not executed)

## Blocked Areas

- LibreOffice conversion: `BLOCKED` — soffice not installed in test environment; all conversion tests use mocks
- Redis rate limiting: `BLOCKED` — Redis unavailable; tests use in-memory fallback
- R2 storage: `BLOCKED` — requires Cloudflare R2 credentials

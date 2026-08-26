# Test Scope

## Tested Features

| Feature | Route/API | Status |
|---------|-----------|--------|
| Home page rendering | GET / | Tested |
| Convert page rendering | GET /convert | Tested |
| Privacy page rendering | GET /privacy | Tested |
| Terms page rendering | GET /terms | Tested |
| 404 error page | GET /nonexistent | Tested |
| Health check | GET /healthz | Tested |
| Robots.txt | GET /robots.txt | Tested |
| Sitemap.xml | GET /sitemap.xml | Tested |
| Favicon | GET /static/favicon.svg | Tested |
| File upload | POST /api/v1/files/upload | Tested |
| File metadata | GET /api/v1/files/{id} | Tested |
| File download | GET /api/v1/files/{id}/download | Tested |
| Format catalog | GET /api/v1/formats | Tested |
| Quota status | GET /api/v1/quota | Tested |
| Job creation | POST /api/v1/jobs/ | Tested |
| Job listing | GET /api/v1/jobs/ | Tested |
| Job status | GET /api/v1/jobs/{id} | Tested |
| Job cancellation | POST /api/v1/jobs/{id}/cancel | Tested |
| Job SSE events | GET /api/v1/jobs/{id}/events | Tested (code review) |
| Rate limiting | Enforced on API endpoints | Tested |
| Daily quota | Enforced on upload | Tested |
| End-to-end conversion | Markdown → PDF | Tested |
| Dark mode toggle | Client-side JS | Tested (code review) |
| Mobile navigation | Client-side JS | Tested (code review) |

## Tested APIs

All REST API v1 endpoints are tested for:
- Valid requests
- Invalid requests (missing fields, wrong types)
- Unauthorized requests
- Missing resources (404)
- Rate limiting (429)
- Quota exceeded (402)
- Unsupported format (415)
- Oversize file (413)

## Tested Authentication

- Guest identity via HttpOnly cookie
- Cookie security flags (HttpOnly, SameSite=Lax, Secure in production)
- Identity derivation from IP + User-Agent (documented limitation)

## Tested Authorization

- Job ownership verification (guest_id matching)
- File access control (download requires file existence)
- Cross-guest access prevention

## Out-of-Scope Areas

- Celery worker (scaffolded but not wired)
- User authentication/registration (User model exists but not actively used)
- R2/S3 storage backend (requires external service)
- Playwright E2E browser tests
- Performance load testing
- Mobile device testing

## Blocked Areas

- Redis-backed rate limiting: Redis unavailable in test environment
- LibreOffice conversion: May not be available in all environments
- R2 storage: Requires Cloudflare credentials

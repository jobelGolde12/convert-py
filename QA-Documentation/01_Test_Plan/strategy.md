# Test Strategy

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, FastAPI |
| Database | SQLite/Turso (libSQL) via SQLAlchemy ORM |
| Conversion Engine | LibreOffice (server-side), pdftotext fallback |
| Storage | Local filesystem / Cloudflare R2 |
| Caching | Redis (with in-memory fallback) |
| Frontend | Server-rendered Jinja2 + vanilla JavaScript |
| Testing | pytest, pytest-asyncio |
| Linting | ruff |
| Type Checking | mypy (strict mode) |

## Testing Methodology

### Test Levels

1. **Unit Tests** — Isolated function-level tests (conversion_service, job_service, quota, storage, analytics, clock, config, exceptions, rate limiting, file_service, conversions_catalog)
2. **Integration Tests** — HTTP-level tests via FastAPI TestClient (files, quota, rate limits, security headers, formats, jobs, SSE events)
3. **Manual/Visual** — Template rendering, responsive design, dark mode, accessibility

### Security Methodology

- OWASP Top 10 checklist review
- Source code analysis for injection, XSS, path traversal, IDOR
- Authentication/authorization boundary testing
- Cookie security validation
- Error message sanitization verification

### Performance Methodology

- N+1 query detection via eager loading review
- Gzip middleware analysis
- Static asset caching verification
- Database indexing review
- Background task isolation (non-blocking job processing)

### Accessibility Methodology

- Semantic HTML audit (landmarks, headings, labels)
- Keyboard navigation testing
- ARIA attribute review
- Color contrast and dark mode review
- Screen reader compatibility (aria-live regions)

## Test Priorities

1. File upload and conversion workflow (core feature)
2. Authentication/authorization boundaries
3. Rate limiting and quota enforcement
4. Error handling and input validation
5. Security headers and CSP
6. Responsive design
7. SEO and structured data

## Limitations

- LibreOffice is not installed in CI; conversion unit tests use mocks
- Redis is unavailable in test env; tests use in-memory fallback
- R2/S3 storage not tested (local storage only)
- Browser-based PDF tools (merge, split, rotate, watermark) are client-only and not tested server-side
- SSE streaming tests cover basic flow but not long-running conversions

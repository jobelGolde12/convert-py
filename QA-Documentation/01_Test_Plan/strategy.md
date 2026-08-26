# Test Strategy

## Testing Methodology

This QA audit follows a structured lifecycle: Discovery → Analysis → Testing → Audit → Documentation → Remediation → Verification. Tests are executed against the application running in a development environment with SQLite and in-memory rate limiting (Redis unavailable).

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI 0.111+, Uvicorn |
| Templating | Jinja2 (server-rendered HTML) |
| Frontend | Vanilla HTML + CSS + JavaScript (no framework) |
| Database | SQLAlchemy 2.0, SQLite |
| Caching/Quotas | Redis (in-memory fallback) |
| Conversion | LibreOffice headless (soffice) |
| Testing | pytest 8.2.0, pytest-asyncio, httpx |
| Linting | Ruff 0.4.4 |
| Type Checking | mypy 1.10.0 (strict mode) |

## Testing Tools

- **pytest**: Unit tests, integration tests, API tests
- **httpx**: HTTP client for TestClient
- **Ruff**: Linting and code quality
- **pip-audit**: Dependency vulnerability scanning
- **Manual code review**: Security, architecture, accessibility

## Test Levels

1. **Unit Tests**: Markdown-to-HTML conversion, catalog detection, content disposition sanitization
2. **API Tests**: Upload, download, job creation, quota, rate limiting, error handling
3. **Page Tests**: HTML rendering, SEO metadata, accessibility landmarks, security headers
4. **End-to-End Tests**: Full markdown-to-PDF conversion pipeline (requires LibreOffice)
5. **Security Tests**: OWASP audit, dependency scan, code review for vulnerabilities
6. **Accessibility Tests**: Semantic HTML, ARIA, keyboard navigation, focus states, contrast

## Testing Priorities

1. Security vulnerabilities (injection, access control, secrets)
2. Data integrity (file handling, database operations)
3. Core functionality (upload, convert, download)
4. Error handling (graceful degradation, safe error messages)
5. Accessibility (WCAG compliance)
6. Performance (response times, resource usage)

## Limitations

- Redis is unavailable in test environment; in-memory fallback is used
- LibreOffice may not be available in all environments (tests skip gracefully)
- E2E browser testing (Playwright) is not executed in this audit
- No external service integration testing (R2/S3 storage)

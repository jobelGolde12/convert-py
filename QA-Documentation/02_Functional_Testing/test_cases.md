# Functional Test Cases

## Page Rendering

| Test ID | Feature | Description | Preconditions | Steps | Expected Result | Priority |
|---------|---------|-------------|---------------|-------|-----------------|----------|
| TC-PAGE-001 | Home page | Home page renders with correct content | None | GET / | 200, HTML content-type, contains "Convert", has canonical link, OG tags, JSON-LD, accessibility landmarks | High |
| TC-PAGE-002 | Convert page | Convert page renders with catalog | None | GET /convert | 200, contains data-catalog attribute, conversion options visible | High |
| TC-PAGE-003 | Privacy page | Privacy page renders | None | GET /privacy | 200, contains "Privacy" | Medium |
| TC-PAGE-004 | Terms page | Terms page renders | None | GET /terms | 200, contains "Terms of use" | Medium |
| TC-PAGE-005 | 404 page | Unknown page returns custom 404 | None | GET /nonexistent | 404, HTML content-type, contains "404" | Medium |
| TC-PAGE-006 | Health check | Health endpoint returns OK | None | GET /healthz | 200, {"status": "ok"} | High |
| TC-PAGE-007 | Robots.txt | Robots.txt is served | None | GET /robots.txt | 200, text/plain, contains "Disallow: /api/" | Low |
| TC-PAGE-008 | Sitemap | Sitemap XML is valid | None | GET /sitemap.xml | 200, application/xml, contains urlset | Low |
| TC-PAGE-009 | Favicon | Favicon SVG is served | None | GET /static/favicon.svg | 200, image/svg+xml | Low |
| TC-PAGE-010 | Security headers | Security headers present | None | GET / | X-Content-Type-Options: nosniff, X-Frame-Options: DENY, Referrer-Policy set | High |

## File Upload

| Test ID | Feature | Description | Preconditions | Steps | Expected Result | Priority |
|---------|---------|-------------|---------------|-------|-----------------|----------|
| TC-UPLOAD-001 | Valid upload | Upload a valid markdown file | None | POST /api/v1/files/upload with file | 200, fileId, filename, sizeBytes, status="ready" | High |
| TC-UPLOAD-002 | Download roundtrip | Download matches uploaded content | File uploaded | GET /api/v1/files/{id}/download | 200, content matches, Content-Disposition set | High |
| TC-UPLOAD-003 | Unsupported type | Reject unsupported file types | None | POST with .exe file | 415 | High |
| TC-UPLOAD-004 | No file | Reject empty upload | None | POST without file | 422 | High |
| TC-UPLOAD-005 | Oversize file | Reject files exceeding format limit | None | Upload 11MB .md file (limit 10MB) | 413, maxSizeMB in response | High |
| TC-UPLOAD-006 | Missing file ID | Return 404 for nonexistent file | None | GET /api/v1/files/nonexistent | 404 | High |
| TC-UPLOAD-007 | Content-Disposition | Sanitize filename in header | None | Upload file with special chars | No CRLF injection, proper RFC 5987 encoding | High |

## Job Management

| Test ID | Feature | Description | Preconditions | Steps | Expected Result | Priority |
|---------|---------|-------------|---------------|-------|-----------------|----------|
| TC-JOB-001 | Missing input | Reject job with missing input file | None | POST with nonexistent input | 404 | High |
| TC-JOB-002 | Client-only rejection | Reject client-only conversions via API | PDF uploaded | POST with pdf→pdf conversion | 422, mentions "browser" | High |
| TC-JOB-003 | Invalid body | Reject malformed job body | None | POST with invalid JSON | 422 | High |
| TC-JOB-004 | Cancel missing | Return 404 for nonexistent job cancel | None | POST /api/v1/jobs/ghost/cancel | 404 | Medium |
| TC-JOB-005 | Empty job list | Return empty list for new guest | None | GET /api/v1/jobs/ | 200, empty jobs array | Medium |
| TC-JOB-006 | E2E conversion | Full markdown to PDF conversion | LibreOffice installed | Upload .md, create job, poll status, download | 200, status=done, progress=100, valid PDF output | High |

## Rate Limiting & Quota

| Test ID | Feature | Description | Preconditions | Steps | Expected Result | Priority |
|---------|---------|-------------|---------------|-------|-----------------|----------|
| TC-RL-001 | Quota shape | Quota endpoint returns correct structure | None | GET /api/v1/quota | 200, limit=5, remaining=5, resetsAt | High |
| TC-RL-002 | Cookie security | Guest cookie has security flags | None | GET /api/v1/quota | Set-Cookie: HttpOnly, SameSite=lax | High |
| TC-RL-003 | Rate limit | Rate limit enforced on API | Set limit to 3 | POST /api/v1/jobs/ 5 times | 429 appears in responses | High |

## Navigation & UI

| Test ID | Feature | Description | Preconditions | Steps | Expected Result | Priority |
|---------|---------|-------------|---------------|-------|-----------------|----------|
| TC-UI-001 | Theme toggle | Dark mode toggle present | None | Check HTML | id="theme-toggle" present | Medium |
| TC-UI-002 | Mobile nav | Mobile navigation present | None | Check HTML | id="menu-toggle", id="mobile-nav" present | Medium |
| TC-UI-003 | Skip link | Skip to content link present | None | Check HTML | "Skip to content" link present | Medium |

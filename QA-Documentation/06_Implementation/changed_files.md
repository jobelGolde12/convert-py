# Changed Files

| File | Change | Reason | Related Task |
|------|--------|--------|-------------|
| `app/api/routes/files.py` | Added alphanumeric sanitization to file extension | Path traversal prevention | TASK-001 |
| `app/api/dependencies/rate_limit.py` | Added HMAC signing/verification of guest ID cookie | Cookie spoofing prevention | TASK-002 |
| `app/main.py` | Added production secret validation in lifespan | Prevent default secrets in production | TASK-003 |
| `app/services/job_service.py` | Added error message sanitization function; applied to _fail_job | Prevent information disclosure | TASK-004 |
| `app/static/css/styles.css` | Added mobile media query for icon button touch targets | WCAG 2.5.8 compliance | TASK-005 |
| `app/services/file_service.py` | Removed dead `verify_signed_upload` and duplicate `file_extension_for` | Code quality | TASK-006, TASK-007 |
| `requirements.txt` | Added missing packages, synced versions | Dependency consistency | TASK-008 |
| `app/templates/convert.html` | Added aria-label to hidden file input | Accessibility | TASK-009 |
| `requirements-dev.txt` | Updated pytest to >=9.0.3, pytest-asyncio to >=0.24.0 | Security vulnerability fix | TASK-010 |

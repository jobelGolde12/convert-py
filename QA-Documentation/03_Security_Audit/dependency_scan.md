# Dependency Security Scan

## Scan Tool

- **Tool**: pip-audit 2.10.1
- **Date**: 2026-08-26
- **Python**: 3.12.3

## Results

| Package | Version | Purpose | Vulnerability | Fix Version | Risk | Implementation Status |
|---------|---------|---------|--------------|-------------|------|----------------------|
| pytest | 8.2.0 | Testing framework | PYSEC-2026-1845 | 9.0.3 | Low (dev only) | Will update |

## Summary

- **Total packages scanned**: All installed packages
- **Vulnerable packages**: 1 (pytest, dev dependency only)
- **Critical vulnerabilities**: 0
- **High vulnerabilities**: 0
- **Medium vulnerabilities**: 0
- **Low vulnerabilities**: 1 (dev-only)

## Production Dependencies

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| fastapi | >=0.111.0 | Web framework | No known vulnerabilities |
| uvicorn | >=0.29.0 | ASGI server | No known vulnerabilities |
| jinja2 | >=3.1.3 | Templating | No known vulnerabilities |
| sqlalchemy | >=2.0.30 | ORM | No known vulnerabilities |
| alembic | >=1.13.1 | Migrations | No known vulnerabilities |
| redis | >=5.0.8 | Redis client | No known vulnerabilities |
| celery | >=5.4.0 | Task queue | No known vulnerabilities |
| pydantic | >=2.7.1 | Validation | No known vulnerabilities |
| pydantic-settings | >=2.2.1 | Settings | No known vulnerabilities |
| python-multipart | >=0.0.9 | File uploads | No known vulnerabilities |
| aiofiles | >=23.3.1 | Async file I/O | No known vulnerabilities |
| sse-starlette | >=2.0.0 | SSE support | No known vulnerabilities |
| pypdf | >=4.2.0 | PDF processing | No known vulnerabilities |
| pillow | >=10.3.0 | Image processing | No known vulnerabilities |
| reportlab | >=4.2.0 | PDF generation | No known vulnerabilities |
| pypandoc | >=1.13 | Document conversion | No known vulnerabilities |
| boto3 | >=1.34.129 | S3/R2 storage | No known vulnerabilities |
| python-dotenv | >=1.0.1 | Env loading | No known vulnerabilities |
| slowapi | >=0.2.4 | Rate limiting | No known vulnerabilities |
| limits | >=3.11.0 | Rate limiting | No known vulnerabilities |
| tenacity | >=9.0.0 | Retries | No known vulnerabilities |

## Notes

- Production dependencies show no known vulnerabilities at time of scan
- The only vulnerability is in pytest (dev dependency), which has no production impact
- Dependency pinning in requirements.txt uses `>=` (minimum version) rather than exact pins, which allows automatic security updates

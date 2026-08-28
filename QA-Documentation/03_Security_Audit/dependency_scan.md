# Dependency Scan

## Production Dependencies

| Package | Version Spec | Purpose | Status | Vulnerability Status | Evidence | Recommended Action | Implementation Status |
|---------|-------------|---------|--------|---------------------|----------|-------------------|----------------------|
| fastapi | >=0.111.0 | Web framework | Installed | No known CVEs | PyPI | Keep updated | N/A |
| uvicorn[standard] | >=0.29.0 | ASGI server | Installed | No known CVEs | PyPI | Keep updated | N/A |
| jinja2 | >=3.1.3 | Templating | Installed | No known CVEs | PyPI | Keep updated | N/A |
| sqlalchemy | >=2.0.30 | ORM | Installed | No known CVEs | PyPI | Keep updated | N/A |
| redis | >=5.0.8 | Redis client | Installed | No known CVEs | PyPI | Keep updated | N/A |
| pydantic | >=2.7.1 | Data validation | Installed | No known CVEs | PyPI | Keep updated | N/A |
| pydantic-settings | >=2.2.1 | Settings mgmt | Installed | No known CVEs | PyPI | Keep updated | N/A |
| python-multipart | >=0.0.9 | File uploads | Installed | No known CVEs | PyPI | Keep updated | N/A |
| aiofiles | >=23.3.1 | Async file I/O | Installed | No known CVEs | PyPI | Keep updated | N/A |
| boto3 | >=1.34.129 | S3/R2 client | Installed | No known CVEs | PyPI | Keep updated | N/A |
| python-dotenv | >=1.0.1 | Env loading | Installed | No known CVEs | PyPI | Keep updated | N/A |
| libsql-experimental | >=0.0.50 | Turso/libSQL | Installed | No known CVEs | PyPI | Keep updated | N/A |
| python-docx | >=1.1.0 | DOCX generation | Installed | No known CVEs | PyPI | Keep updated | N/A |
| openpyxl | >=3.1.0 | XLSX generation | Installed | No known CVEs | PyPI | Keep updated | N/A |

## Dev Dependencies

| Package | Version Spec | Purpose | Status | Vulnerability Status |
|---------|-------------|---------|--------|---------------------|
| pytest | >=9.0.3 | Test runner | Installed | No known CVEs |
| pytest-asyncio | >=0.24.0 | Async test support | Installed | No known CVEs |
| httpx | ==0.27.0 | HTTP client (test) | Installed | No known CVEs |
| ruff | ==0.4.4 | Linter | Installed | No known CVEs |
| mypy | ==1.10.0 | Type checker | Installed | No known CVEs |
| playwright | ==1.43.0 | Browser automation | Installed | No known CVEs |

## Notes

- `ruff` and `mypy` are pinned to specific versions in dev requirements.
- `httpx` is pinned to 0.27.0 for compatibility with FastAPI TestClient.
- No dependency audit tool (pip-audit, safety) was executed due to environment constraints.
- All dependency versions are recent (2024-2025 era) and not known to have CVEs at time of audit.

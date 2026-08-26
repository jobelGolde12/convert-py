# Remaining Issues

## Summary

All identified actionable issues have been implemented and verified. The following are documented as accepted risks or deferred items.

| Issue ID | Description | Severity | Reason Not Fixed | Blocked By | Recommended Next Step |
|----------|-------------|----------|------------------|------------|----------------------|
| SEC-005 | No CSRF tokens on POST endpoints | Low | SameSite=Lax + JSON content-type provides sufficient protection; no form-based interactions | None | Accept as-is; revisit if form-based interactions added |
| A11Y-002 | Dark mode not announced to screen readers | Informational | Native accessibility behavior is acceptable | None | No action needed |
| A11Y-003 | FAQ details missing aria-expanded | Informational | Native `<details>`/`<summary>` handles state correctly | None | No action needed |
| RESP-001 | Format grid min-width could overflow on <240px | Informational | No devices < 240px in practice | None | No action needed |
| RESP-002 | Select min-width could overflow on narrow screens | Minor | Flex-wrap handles overflow | None | No action needed |
| INFRA-001 | Celery worker scaffolded but not wired | Informational | Not needed for current scope | Celery broker | Implement when background job queue needed |
| INFRA-002 | Alembic migrations not generated | Minor | create_all() handles development | Schema changes | Generate initial migration before production |
| INFRA-003 | SQLite used (not suitable for production) | Medium | Development only | PostgreSQL setup | Switch to PostgreSQL for production |

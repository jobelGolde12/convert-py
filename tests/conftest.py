from __future__ import annotations

import os
import tempfile

# Isolate environment BEFORE app modules are imported.
_TMP = tempfile.mkdtemp(prefix="convert-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["LOCAL_STORAGE_ROOT"] = os.path.join(_TMP, "storage")
os.environ["REDIS_URL"] = "redis://127.0.0.1:1"  # unreachable -> memory fallback
os.environ["ENV"] = "development"
# Force tests to use local SQLite, never Turso
os.environ["TURSO_DATABASE_URL"] = ""
os.environ["TURSO_AUTH_TOKEN"] = ""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolated_memory_state():
    """Reset the in-memory quota/rate-limit store around every test."""
    import app.services.quota_service as quota_service

    quota_service._mem._windows.clear()
    yield
    quota_service._mem._windows.clear()


@pytest.fixture(autouse=True)
def _isolated_db():
    """Truncate DB tables between tests to ensure isolation."""
    yield
    try:
        from app.core.database import SessionLocal
        from app.models.models import Conversion, File, Job, Task

        if SessionLocal is None:
            return
        db = SessionLocal()
        try:
            # Delete in FK order
            db.query(Conversion).delete()
            db.query(Task).delete()
            db.query(Job).delete()
            db.query(File).delete()
            db.commit()
        finally:
            db.close()
    except Exception:
        pass


@pytest.fixture()
def client(monkeypatch):
    # Force in-memory quota/rate-limit state so tests never depend on Redis.
    import app.services.quota_service as quota_service

    monkeypatch.setattr(quota_service, "_redis_client", lambda: None)

    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c

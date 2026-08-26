from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator
from urllib.parse import parse_qs, urlparse

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("convert.db")


class _LibSQLProxy:
    """Wrapper around libsql Connection that stubs out methods
    SQLAlchemy's SQLite dialect expects but libsql doesn't implement."""

    def __init__(self, conn: Any):
        object.__setattr__(self, "_conn", conn)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_conn"), name)

    def create_function(self, *args, **kwargs):
        pass


def _make_engine():
    """Create the SQLAlchemy engine.

    When TURSO_DATABASE_URL + TURSO_AUTH_TOKEN are set, connects to Turso
    via libsql-experimental.  Otherwise falls back to local SQLite for
    development convenience.
    """
    if settings.use_turso:
        return _make_turso_engine()
    return _make_sqlite_engine()


def _make_turso_engine():
    import libsql_experimental as libsql

    raw_url = settings.turso_database_url
    token = settings.turso_auth_token

    # Normalise: accept bare "db-host.turso.io" or full "libsql://..." forms
    if not raw_url.startswith(("libsql://", "sqlite+libsql://")):
        raw_url = f"libsql://{raw_url}"

    parsed = urlparse(raw_url.replace("sqlite+libsql://", "libsql://"))
    host = parsed.hostname or ""
    database = parsed.path.lstrip("/") or ""
    auth_token = token or parsed.password or ""

    query = parse_qs(parsed.query)
    sync_url = query.get("sync_url", [None])[0]
    local_path = query.get("local_path", [None])[0]

    def _connect():
        if sync_url:
            db_path = local_path or f"/tmp/{database}.db"
            logger.info("Turso embedded replica: local=%s sync=%s", db_path, sync_url)
            conn = libsql.connect(
                database=db_path,
                sync_url=sync_url,
                auth_token=auth_token,
            )
        else:
            libsql_url = f"libsql://{host}"
            if database:
                libsql_url += f"/{database}"
            logger.info("Turso remote: %s/%s", host, database)
            conn = libsql.connect(database=libsql_url, auth_token=auth_token)
        return _LibSQLProxy(conn)

    engine = create_engine(
        "sqlite://",
        creator=_connect,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
    _attach_pragmas(engine)
    return engine


def _make_sqlite_engine():
    logger.info("Using local SQLite: %s", settings.database_url)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
        pool_pre_ping=True,
        echo=settings.env == "development",
    )
    _attach_pragmas(engine)
    return engine


def _attach_pragmas(engine):
    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_conn, connection_record):
        try:
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA busy_timeout=5000")
        except Exception:
            pass


try:
    engine = _make_engine()
except Exception:
    logger.warning("Database engine creation failed at startup; will retry on first use.", exc_info=True)
    engine = None  # type: ignore[assignment]

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None  # type: ignore[arg-type]


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database not initialised — no engine available.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database not initialised — no engine available.")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Import models so they register on Base."""
    global engine, SessionLocal

    # If engine failed at import, retry now.
    if engine is None:
        try:
            engine = _make_engine()
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        except Exception:
            logger.error("Database engine creation failed; API routes will be unavailable.", exc_info=True)
            return

    from app.models import models  # noqa: F401

    models.Base.metadata.create_all(bind=engine)
    backend = "turso" if settings.use_turso else "sqlite"
    logger.info("Database initialized (%s)", backend)

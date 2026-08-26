from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("convert.db")


def _make_engine():
    """Create the SQLAlchemy engine, using libsql when Turso credentials are configured."""
    # Prefer Turso when credentials are provided
    if settings.turso_database_url and settings.turso_auth_token:
        url = settings.turso_database_url
        token = settings.turso_auth_token
    else:
        url = settings.database_url
        token = ""

    # Turso / libSQL connection
    if url.startswith("sqlite+libsql://") or url.startswith("libsql://") or (token and "turso.io" in url):
        import libsql_experimental as libsql
        from urllib.parse import urlparse, parse_qs

        # Normalize URL
        if not url.startswith(("libsql://", "sqlite+libsql://")):
            # Raw turso URL like "libsql://db-name-org.turso.io"
            url = f"libsql://{url}" if not url.startswith("libsql://") else url

        parsed = urlparse(url.replace("sqlite+libsql://", "libsql://"))
        host = parsed.hostname or ""
        port = parsed.port or 3306
        database = parsed.path.lstrip("/") or ""
        auth_token = token or parsed.password or ""

        # Determine sync mode
        query = parse_qs(parsed.query)
        sync_url = query.get("sync_url", [None])[0]
        local_path = query.get("local_path", [None])[0]

        def _connect():
            if sync_url:
                db_path = local_path or f"/tmp/{database}.db"
                return libsql.connect(
                    database=db_path,
                    sync_url=sync_url,
                    auth_token=auth_token,
                )
            elif host:
                libsql_url = f"libsql://{host}:{port}/{database}"
                if auth_token:
                    libsql_url += f"?authToken={auth_token}"
                return libsql.connect(database=libsql_url)
            else:
                return libsql.connect(database=database)

        engine = create_engine(
            "sqlite://",
            creator=_connect,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )
    else:
        # Standard SQLite (development)
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
            pool_pre_ping=True,
            echo=settings.env == "development",
        )

    # Enable WAL mode for better concurrent read performance (SQLite only)
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        try:
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA busy_timeout=5000")
        except Exception:
            pass  # Not all backends support PRAGMA

    return engine


engine = _make_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
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
    from app.models import models  # noqa: F401

    models.Base.metadata.create_all(bind=engine)
    logger.info("Database initialized (%s)", settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url)

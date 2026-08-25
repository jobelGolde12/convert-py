from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime.datetime:
    """Naive UTC timestamp (SQLite stores naive datetimes)."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    image: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="user")
    plan: Mapped[str] = mapped_column(String, default="free")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    files: Mapped[list["File"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    storage_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    bucket: Mapped[str] = mapped_column(String, default="local")
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="uploading")
    source: Mapped[str] = mapped_column(String, default="upload")
    retention_until: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User | None] = relationship(back_populates="files")
    input_tasks: Mapped[list["Task"]] = relationship(
        foreign_keys="Task.input_file_id", back_populates="input"
    )
    output_tasks: Mapped[list["Task"]] = relationship(
        foreign_keys="Task.output_file_id", back_populates="output"
    )

    __table_args__ = (
        Index("idx_files_user_created", "user_id", "created_at"),
        Index("idx_files_status_retention", "status", "retention_until"),
        Index("idx_files_checksum", "checksum_sha256"),
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    guest_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="queued")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)
    timings_ms: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User | None] = relationship(back_populates="jobs")
    tasks: Mapped[list["Task"]] = relationship(back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_jobs_user_created", "user_id", "created_at"),
        Index("idx_jobs_guest_created", "guest_id", "created_at"),
        Index("idx_jobs_status_created", "status", "created_at"),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(
        String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    operation: Mapped[str] = mapped_column(String, nullable=False)
    engine: Mapped[str | None] = mapped_column(String, nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String, nullable=True)
    input_file_id: Mapped[str | None] = mapped_column(String, ForeignKey("files.id"), nullable=True)
    output_file_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("files.id"), nullable=True
    )
    options: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="waiting")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    job: Mapped[Job] = relationship(back_populates="tasks")
    input: Mapped[File | None] = relationship(
        foreign_keys=input_file_id, back_populates="input_tasks"
    )
    output: Mapped[File | None] = relationship(
        foreign_keys=output_file_id, back_populates="output_tasks"
    )

    __table_args__ = (
        Index("idx_tasks_job", "job_id"),
        Index("idx_tasks_status_created", "status", "created_at"),
        Index("idx_tasks_input", "input_file_id"),
    )


class Conversion(Base):
    __tablename__ = "conversions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    job_id: Mapped[str | None] = mapped_column(String, ForeignKey("jobs.id"), nullable=True)
    source_format: Mapped[str] = mapped_column(String, nullable=False)
    target_format: Mapped[str] = mapped_column(String, nullable=False)
    engine: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="done")
    input_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credits_used: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    date: Mapped[str] = mapped_column(String, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    bytes_in: Mapped[int] = mapped_column(Integer, default=0)
    bytes_out: Mapped[int] = mapped_column(Integer, default=0)
    credits_used: Mapped[int] = mapped_column(Integer, default=0)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_usage_user_date"),
        Index("idx_usage_date", "date"),
    )

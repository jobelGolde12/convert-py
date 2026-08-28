from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import InvalidDataError, NotFoundError, OfficeError, UnsupportedConversionError, UnsupportedFormatError
from app.models.models import Base, File, Job, Task
from app.services.job_service import _convert_with_fallback, _sanitize_error_message, create_server_job, get_job_for_api


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/job_unit.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Need storage isolation
    import os

    os.environ["LOCAL_STORAGE_ROOT"] = str(tmp_path / "storage")
    yield session
    session.close()
    engine.dispose()


def _make_file(session, filename="doc.docx", status="ready"):
    import datetime

    f = File(
        id=f"file-{filename}-{status}",
        storage_key=f"files/file-{filename}-{status}/file.docx",
        bucket="local",
        filename=filename,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size_bytes=100,
        status=status,
        retention_until=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
    )
    session.add(f)
    session.commit()
    return f


class TestSanitizeErrorMessage:
    def test_removes_unix_path(self):
        msg = "failed at /tmp/lo-profiles/convert-123/in.docx: error"
        sanitized = _sanitize_error_message(msg)
        assert "/tmp/lo-profiles" not in sanitized
        assert "[path]" in sanitized

    def test_removes_windows_path(self):
        msg = r"failed at C:\Users\test\file.docx error"
        sanitized = _sanitize_error_message(msg)
        assert "C:\\Users" not in sanitized

    def test_removes_stack_frame(self):
        msg = 'File "/app/app/services/job_service.py", line 10, in foo'
        sanitized = _sanitize_error_message(msg)
        assert "/app/app/services/job_service.py" not in sanitized
        assert '[hidden]' in sanitized

    def test_truncates_to_200(self):
        long_msg = "x" * 500
        assert len(_sanitize_error_message(long_msg)) <= 200

    def test_clean_message_unchanged(self):
        msg = "Simple error without paths"
        assert _sanitize_error_message(msg) == msg


class TestCreateServerJob:
    def test_success_docx_to_pdf(self, db_session):
        f = _make_file(db_session, "report.docx")
        job, conv = create_server_job(db_session, [{"operation": "convert", "input": f.id, "outputFormat": "pdf"}])
        assert job.status == "queued"
        assert conv.id == "docx-pdf"
        assert len(job.tasks) == 1 or db_session.query(Task).filter(Task.job_id == job.id).count() == 1

    def test_invalid_operation_rejected(self, db_session):
        f = _make_file(db_session, "a.docx")
        with pytest.raises(InvalidDataError):
            create_server_job(db_session, [{"operation": "merge", "input": f.id, "outputFormat": "pdf"}])

    def test_empty_tasks_rejected(self, db_session):
        with pytest.raises(InvalidDataError):
            create_server_job(db_session, [])

    def test_multiple_tasks_rejected(self, db_session):
        f = _make_file(db_session, "a.docx")
        with pytest.raises(InvalidDataError):
            create_server_job(
                db_session,
                [
                    {"operation": "convert", "input": f.id, "outputFormat": "pdf"},
                    {"operation": "convert", "input": f.id, "outputFormat": "pdf"},
                ],
            )

    def test_missing_input_file(self, db_session):
        with pytest.raises(NotFoundError):
            create_server_job(db_session, [{"operation": "convert", "input": "ghost-id", "outputFormat": "pdf"}])

    def test_file_not_ready(self, db_session):
        f = _make_file(db_session, "pending.docx", status="uploading")
        with pytest.raises(Exception) as exc:
            create_server_job(db_session, [{"operation": "convert", "input": f.id, "outputFormat": "pdf"}])
        assert exc.value.status_code == 409

    def test_unsupported_source_format(self, db_session):
        import datetime

        f = File(
            id="file-unknown",
            storage_key="files/file-unknown/file.xyz",
            bucket="local",
            filename="file.xyz",
            mime_type="application/x-unknown",
            size_bytes=100,
            status="ready",
            retention_until=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
        )
        db_session.add(f)
        db_session.commit()
        # file.xyz is not in catalog -> detect_format returns None
        with pytest.raises(UnsupportedFormatError):
            create_server_job(db_session, [{"operation": "convert", "input": f.id, "outputFormat": "pdf"}])

    def test_unsupported_conversion(self, db_session):
        f = _make_file(db_session, "a.docx")
        with pytest.raises(UnsupportedConversionError):
            create_server_job(db_session, [{"operation": "convert", "input": f.id, "outputFormat": "nonexistent"}])

    def test_client_only_conversion_rejected(self, db_session):
        import datetime

        f = File(
            id="file-pdf-client",
            storage_key="files/file-pdf-client/file.pdf",
            bucket="local",
            filename="doc.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            status="ready",
            retention_until=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
        )
        db_session.add(f)
        db_session.commit()
        with pytest.raises(UnsupportedConversionError, match="browser"):
            create_server_job(db_session, [{"operation": "convert", "input": f.id, "outputFormat": "pdf"}])

    def test_with_guest_id_and_idempotency(self, db_session):
        f = _make_file(db_session, "b.docx")
        job, _ = create_server_job(
            db_session,
            [{"operation": "convert", "input": f.id, "outputFormat": "pdf"}],
            guest_id="guest-123",
            idempotency_key="idem-key-1",
        )
        assert job.guest_id == "guest-123"
        assert job.idempotency_key == "idem-key-1"


class TestGetJobForApi:
    def test_returns_none_for_missing(self, db_session):
        assert get_job_for_api(db_session, "ghost") is None

    def test_returns_structure(self, db_session):
        f = _make_file(db_session, "c.docx")
        job, _ = create_server_job(db_session, [{"operation": "convert", "input": f.id, "outputFormat": "pdf"}])
        result = get_job_for_api(db_session, job.id)
        assert result is not None
        assert result["id"] == job.id
        assert result["status"] == "queued"
        assert "progress" in result
        assert "outputs" in result
        assert "tasks" in result
        assert result["outputs"] == []
        assert len(result["tasks"]) == 1

    def test_done_progress_100(self, db_session):
        f = _make_file(db_session, "d.docx")
        job, _ = create_server_job(db_session, [{"operation": "convert", "input": f.id, "outputFormat": "pdf"}])
        job.status = "done"
        db_session.commit()
        result = get_job_for_api(db_session, job.id)
        assert result["progress"] == 100


class TestConvertWithFallback:
    def test_uses_soffice_when_it_succeeds(self, tmp_path):
        from app.services.conversion_service import ConversionResult

        # Mock soffice to produce a valid output file
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        (out_dir / "input.docx").write_bytes(b"PK\x03\x04 fake zip")

        soffice_result = ConversionResult(str(out_dir / "input.docx"), "", "")
        fallback_fn = MagicMock(side_effect=AssertionError("fallback should not be called"))

        with patch("app.services.job_service.convert_with_soffice", return_value=soffice_result):
            result = _convert_with_fallback(
                str(tmp_path / "input.pdf"), str(out_dir), "docx", fallback_fn, "PDF→DOCX"
            )
        assert result.output_path.endswith(".docx")
        fallback_fn.assert_not_called()

    def test_uses_fallback_when_soffice_fails(self, tmp_path):
        from app.services.conversion_service import ConversionResult

        fallback_result = ConversionResult(str(tmp_path / "fallback.docx"), "", "")
        fallback_fn = MagicMock(return_value=fallback_result)

        # Mock convert_with_soffice to raise OfficeError
        with patch(
            "app.services.job_service.convert_with_soffice",
            side_effect=OfficeError("soffice not found", "ENGINE_UNAVAILABLE"),
        ):
            result = _convert_with_fallback(
                str(tmp_path / "input.pdf"), str(tmp_path / "out"),
                "docx", fallback_fn, "PDF→DOCX",
            )
        assert result == fallback_result
        fallback_fn.assert_called_once()

    def test_uses_fallback_when_output_invalid(self, tmp_path):
        from app.services.conversion_service import ConversionResult

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        # Write invalid output (not a valid docx)
        (out_dir / "input.docx").write_bytes(b"not a zip")

        soffice_result = ConversionResult(str(out_dir / "input.docx"), "", "")
        fallback_result = ConversionResult(str(tmp_path / "fallback.docx"), "", "")
        fallback_fn = MagicMock(return_value=fallback_result)

        with patch("app.services.job_service.convert_with_soffice", return_value=soffice_result):
            result = _convert_with_fallback(
                str(tmp_path / "input.pdf"), str(out_dir),
                "docx", fallback_fn, "PDF→DOCX",
            )
        assert result == fallback_result
        fallback_fn.assert_called_once()

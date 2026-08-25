from __future__ import annotations

import time

import pytest


pytestmark = pytest.mark.usefixtures("client")


@pytest.fixture()
def guest(client):
    """Prime the guest cookie so subsequent requests share one identity."""
    client.get("/api/v1/quota")
    return None


class TestFormats:
    def test_formats_catalog(self, client):
        r = client.get("/api/v1/formats")
        assert r.status_code == 200
        body = r.json()
        assert len(body["conversions"]) >= 20
        assert any(c["id"] == "docx-pdf" for c in body["conversions"])
        formats = {f["format"] for f in body["formats"]}
        assert {"pdf", "docx", "xlsx", "pptx", "md"} <= formats


class TestQuota:
    def test_quota_shape(self, client):
        r = client.get("/api/v1/quota")
        assert r.status_code == 200
        body = r.json()
        assert body["limit"] == 5
        assert body["remaining"] == 5
        assert "resetsAt" in body

    def test_guest_cookie_is_set_httponly(self, client):
        r = client.get("/api/v1/quota")
        cookie_header = r.headers.get("set-cookie", "")
        assert "convert-guest-id=" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header


class TestUpload:
    def test_upload_and_fetch(self, client):
        content = b"# Title\n\nSome **bold** text.\n"
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("notes.md", content, "text/markdown")},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "ready"
        assert body["sizeBytes"] == len(content)

        r2 = client.get(f"/api/v1/files/{body['fileId']}")
        assert r2.status_code == 200
        assert r2.json()["filename"] == "notes.md"

    def test_download_roundtrip(self, client):
        content = b"hello conversion world"
        up = client.post(
            "/api/v1/files/upload",
            files={"file": ("hi.txt", content, "text/plain")},
        ).json()
        dl = client.get(f"/api/v1/files/{up['fileId']}/download")
        assert dl.status_code == 200
        assert dl.content == content
        assert 'filename="hi.txt"' in dl.headers["content-disposition"]

    def test_unsupported_extension_415(self, client):
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("evil.exe", b"MZ...", "application/octet-stream")},
        )
        assert r.status_code == 415

    def test_no_file_422(self, client):
        r = client.post("/api/v1/files/upload")
        assert r.status_code == 422

    def test_oversize_stream_rejected_413(self, client):
        # markdown max size is 10 MB; send 11 MB
        big = b"a" * (11 * 1024 * 1024)
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("big.md", big, "text/markdown")},
        )
        assert r.status_code == 413
        assert r.json()["detail"]["maxSizeMB"] == 10

    def test_missing_file_after_upload_404(self, client):
        r = client.get("/api/v1/files/nonexistent-id")
        assert r.status_code == 404

    def test_content_disposition_sanitized(self, client):
        from app.services.file_service import content_disposition

        # CRLF injection attempt is neutralized
        header = content_disposition('evil\r\nX-Inject: 1".txt')
        assert "\r" not in header and "\n" not in header
        assert header.startswith("attachment;")
        # non-ASCII gets an RFC 5987 fallback
        header2 = content_disposition("résumé.pdf")
        assert "filename*=UTF-8''r%C3%A9sum%C3%A9.pdf" in header2
        assert header2.startswith('attachment; filename="resume.pdf"')


class TestJobsValidation:
    def _upload(self, client, name="in.md", data=b"x"):
        return client.post(
            "/api/v1/files/upload",
            files={"file": (name, data, "application/octet-stream")},
        ).json()["fileId"]

    def test_job_for_missing_input_404(self, client):
        r = client.post(
            "/api/v1/jobs/",
            json={"tasks": [{"operation": "convert", "input": "ghost", "outputFormat": "pdf"}]},
        )
        assert r.status_code == 404

    def test_client_only_conversion_rejected_422(self, client):
        # pdf -> pdf maps to the client-only merge tool
        pdf_id = self._upload(client, name="in.pdf")
        r = client.post(
            "/api/v1/jobs/",
            json={"tasks": [{"operation": "convert", "input": pdf_id, "outputFormat": "pdf"}]},
        )
        assert r.status_code == 422
        assert "browser" in r.text.lower()

    def test_invalid_body_422(self, client):
        r = client.post("/api/v1/jobs/", json={"nope": True})
        assert r.status_code == 422

    def test_cancel_missing_job_404(self, client):
        r = client.post("/api/v1/jobs/ghost/cancel")
        assert r.status_code == 404

    def test_jobs_list_empty_for_new_guest(self, client):
        r = client.get("/api/v1/jobs/")
        assert r.status_code == 200
        assert r.json()["jobs"] == []


class TestRateLimit:
    def test_rate_limit_kicks_in(self, client, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "anon_req_per_min", 3)
        statuses = []
        for _ in range(5):
            r = client.post(
                "/api/v1/jobs/",
                json={"tasks": [{"operation": "convert", "input": "x", "outputFormat": "pdf"}]},
            )
            statuses.append(r.status_code)
        assert 429 in statuses


class TestEndToEndConversion:
    @pytest.fixture()
    def soffice_available(self):
        import shutil

        if shutil.which("soffice") is None:
            pytest.skip("LibreOffice not installed")
        return True

    def test_markdown_to_pdf_end_to_end(self, client, soffice_available):
        md = (
            "# Quarterly Report\n\n"
            "- revenue is up\n"
            "- costs are down\n\n"
            "See [the docs](https://example.com) for details."
        ).encode()
        up = client.post(
            "/api/v1/files/upload",
            files={"file": ("report.md", md, "text/markdown")},
        )
        assert up.status_code == 200, up.text
        file_id = up.json()["fileId"]

        job_res = client.post(
            "/api/v1/jobs/",
            json={"tasks": [{"operation": "convert", "input": file_id, "outputFormat": "pdf"}]},
        )
        assert job_res.status_code == 200, job_res.text
        job = job_res.json()
        assert job["conversion"]["location"] == "server"
        job_id = job["id"]

        state = None
        for _ in range(120):  # generous timeout for CI
            poll = client.get(f"/api/v1/jobs/{job_id}")
            assert poll.status_code == 200
            state = poll.json()
            if state["status"] in {"done", "error"}:
                break
            time.sleep(0.25)

        assert state is not None, "job never reported a terminal state"
        if state["status"] == "error":
            pytest.fail(f"conversion failed: {state['error']}")
        assert state["progress"] == 100
        outputs = state["outputs"]
        assert outputs and outputs[0]["downloadUrl"]

        download = client.get(outputs[0]["downloadUrl"])
        assert download.status_code == 200
        assert download.content[:4] == b"%PDF"
        assert "report.pdf" in download.headers["content-disposition"]

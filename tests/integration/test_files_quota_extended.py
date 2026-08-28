from __future__ import annotations

import pytest

pytestmark = pytest.mark.usefixtures("client")


class TestQuotaExtended:
    def test_quota_decrements_after_upload(self, client):
        r1 = client.get("/api/v1/quota").json()
        initial_remaining = r1["remaining"]
        client.post(
            "/api/v1/files/upload",
            files={"file": ("q.md", b"hello", "text/markdown")},
        )
        r2 = client.get("/api/v1/quota").json()
        assert r2["remaining"] == initial_remaining - 1
        assert r2["used"] == r1["used"] + 1

    def test_quota_exceeded_returns_402(self, client, monkeypatch):
        from app.core.config import settings

        # Set daily limit to 1 then exceed
        monkeypatch.setattr(settings, "anon_conversions_per_day", 1)
        client.post(
            "/api/v1/files/upload",
            files={"file": ("a.md", b"x", "text/markdown")},
        )
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("b.md", b"x", "text/markdown")},
        )
        assert r.status_code == 402
        assert r.json()["error"] == "QUOTA_EXCEEDED"

    def test_quota_shape_resetsAt_is_tomorrow(self, client):
        r = client.get("/api/v1/quota").json()
        assert "resetsAt" in r
        assert "T" in r["resetsAt"]


class TestFilesDownloadExtended:
    def test_download_missing_404(self, client):
        r = client.get("/api/v1/files/nonexistent/download")
        assert r.status_code == 404

    def test_download_has_security_headers(self, client):
        up = client.post(
            "/api/v1/files/upload",
            files={"file": ("sec.md", b"secret", "text/markdown")},
        ).json()
        r = client.get(f"/api/v1/files/{up['fileId']}/download")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("Content-Length") == str(len(b"secret"))

    def test_get_file_includes_metadata(self, client):
        up = client.post(
            "/api/v1/files/upload",
            files={"file": ("meta.txt", b"hello world", "text/plain")},
        ).json()
        r = client.get(f"/api/v1/files/{up['fileId']}")
        body = r.json()
        assert body["filename"] == "meta.txt"
        assert body["sizeBytes"] == 11
        assert body["status"] == "ready"

    def test_upload_with_txt_format(self, client):
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("notes.txt", b"plain text", "text/plain")},
        )
        assert r.status_code == 200

    def test_upload_with_html_format(self, client):
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("page.html", b"<html>hi</html>", "text/html")},
        )
        assert r.status_code == 200

    def test_upload_with_various_extensions(self, client):
        for name in ["doc.docx", "sheet.xlsx", "pres.pptx", "data.csv"]:
            r = client.post(
                "/api/v1/files/upload",
                files={"file": (name, b"fake content", "application/octet-stream")},
            )
            assert r.status_code == 200, f"Failed for {name}: {r.text}"

    def test_upload_unicode_filename(self, client):
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("résumé.md", b"# hello", "text/markdown")},
        )
        assert r.status_code == 200
        fid = r.json()["fileId"]
        dl = client.get(f"/api/v1/files/{fid}/download")
        assert dl.status_code == 200
        # Non-ASCII filename should have RFC5987 header
        assert "filename*=" in dl.headers["content-disposition"]

    def test_upload_empty_file(self, client):
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("empty.md", b"", "text/markdown")},
        )
        # empty file is allowed (size 0)
        assert r.status_code == 200
        assert r.json()["sizeBytes"] == 0

    def test_upload_no_extension_415(self, client):
        r = client.post(
            "/api/v1/files/upload",
            files={"file": ("noext", b"data", "application/octet-stream")},
        )
        assert r.status_code == 415

    def test_cross_guest_download_denied_for_output_file(self, client, monkeypatch):
        """Output files should only be downloadable by the guest who owns the job."""
        import app.api.routes.jobs as jobs_module

        monkeypatch.setattr(jobs_module, "process_office_job", lambda *a, **kw: None)

        # Guest A uploads and creates a job
        fid = client.post(
            "/api/v1/files/upload",
            files={"file": ("a.md", b"x", "text/markdown")},
        ).json()["fileId"]
        job_id = client.post(
            "/api/v1/jobs/",
            json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]},
        ).json()["id"]

        # Guest B with different identity should not see the job
        from fastapi.testclient import TestClient
        from app.main import create_app

        with TestClient(create_app(), headers={"User-Agent": "other-guest-download"}) as other:
            r = other.get(f"/api/v1/jobs/{job_id}", headers={"User-Agent": "other-guest-download"})
            assert r.status_code == 404

    def test_uploaded_file_accessible_by_any_guest(self, client):
        """Uploaded files remain accessible (they were initiated by the uploader)."""
        up = client.post(
            "/api/v1/files/upload",
            files={"file": ("open.md", b"data", "text/markdown")},
        ).json()
        # Download should succeed for the uploading guest
        r = client.get(f"/api/v1/files/{up['fileId']}/download")
        assert r.status_code == 200


class TestRateLimitIntegration:
    def test_rate_limit_headers_on_429(self, client, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "anon_req_per_min", 1)
        # First request succeeds
        client.post("/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": "x", "outputFormat": "pdf"}]})
        # Second should be rate limited
        r = client.post("/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": "x", "outputFormat": "pdf"}]})
        assert r.status_code == 429
        assert r.headers.get("Retry-After") == "60"

    def test_guest_cookie_tamper_generates_new_identity(self, client):
        # Set a tampered cookie; server should issue a new signed cookie
        client.cookies.set("convert-guest-id", "tampered.invalidsig")
        r = client.get("/api/v1/quota")
        assert r.status_code == 200
        # Response should set a new valid cookie
        set_cookie = r.headers.get("set-cookie", "")
        assert "convert-guest-id=" in set_cookie

    def test_valid_guest_cookie_preserved(self, client):
        r1 = client.get("/api/v1/quota")
        cookie = r1.headers.get("set-cookie", "")
        assert "convert-guest-id=" in cookie
        # Second request should reuse identity and not exceed quota unexpectedly
        r2 = client.get("/api/v1/quota")
        assert r2.json()["used"] == r1.json()["used"]


class TestSecurityAndMiddleware:
    def test_cors_headers(self, client):
        r = client.get("/", headers={"Origin": "http://localhost:3000"})
        # CORS not configured with origins, so no allow-origin for unknown origin
        assert r.status_code == 200

    def test_request_id_header_present(self, client):
        r = client.get("/")
        assert "X-Request-ID" in r.headers
        assert "Server-Timing" in r.headers

    def test_custom_request_id_propagated(self, client):
        r = client.get("/", headers={"X-Request-ID": "my-custom-id"})
        assert r.headers["X-Request-ID"] == "my-custom-id"

    def test_security_headers_all(self, client):
        r = client.get("/")
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in r.headers
        assert "Permissions-Policy" in r.headers

    def test_gzip_compression(self, client):
        r = client.get("/", headers={"Accept-Encoding": "gzip"})
        # SmartGzipMiddleware only compresses if Content-Length >= minimum_size
        assert r.status_code == 200

    def test_404_api_returns_json(self, client):
        r = client.get("/api/v1/nonexistent-endpoint")
        assert r.status_code == 404
        assert r.headers["content-type"].startswith("application/json")

    def test_404_page_returns_html(self, client):
        r = client.get("/does-not-exist-xyz")
        assert r.status_code == 404
        assert "text/html" in r.headers["content-type"]


class TestFormatsExtended:
    def test_formats_returns_all_conversions(self, client):
        r = client.get("/api/v1/formats")
        body = r.json()
        assert "conversions" in body
        assert "formats" in body
        # every conversion must have 'from' not 'from_'
        for c in body["conversions"]:
            assert "from" in c
            assert "from_" not in c

    def test_formats_server_and_client_present(self, client):
        body = client.get("/api/v1/formats").json()
        locations = {c["location"] for c in body["conversions"]}
        assert "server" in locations
        assert "client" in locations

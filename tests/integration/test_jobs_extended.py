from __future__ import annotations

import pytest


pytestmark = pytest.mark.usefixtures("client")


class TestJobsListPagination:
    def _upload(self, client, name="in.md", data=b"x"):
        return client.post(
            "/api/v1/files/upload",
            files={"file": (name, data, "application/octet-stream")},
        ).json()["fileId"]

    def test_list_returns_created_jobs(self, client):
        fid = self._upload(client)
        client.post("/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]})
        r = client.get("/api/v1/jobs/")
        assert r.status_code == 200
        body = r.json()
        assert len(body["jobs"]) == 1
        assert "nextCursor" in body

    def test_list_pagination_with_limit(self, client):
        fids = [self._upload(client, name=f"f{i}.md", data=b"x") for i in range(3)]
        for fid in fids:
            client.post("/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]})
        r = client.get("/api/v1/jobs/?limit=2")
        assert r.status_code == 200
        body = r.json()
        assert len(body["jobs"]) == 2
        assert body["nextCursor"] is not None
        # fetch next page
        r2 = client.get(f"/api/v1/jobs/?limit=2&cursor={body['nextCursor']}")
        assert r2.status_code == 200
        assert len(r2.json()["jobs"]) == 1

    def test_list_limit_clamped(self, client):
        r = client.get("/api/v1/jobs/?limit=9999")
        assert r.status_code == 200
        r2 = client.get("/api/v1/jobs/?limit=0")
        assert r2.status_code == 200

    def test_list_invalid_cursor_does_not_crash(self, client):
        r = client.get("/api/v1/jobs/?cursor=not-a-timestamp")
        assert r.status_code == 200

    def test_list_isolation_per_guest(self, client):
        from fastapi.testclient import TestClient

        from app.main import create_app

        # Use distinct User-Agent so identity differs from main client
        with TestClient(create_app(), headers={"User-Agent": "other-guest-1"}) as other:
            up = other.post(
                "/api/v1/files/upload",
                files={"file": ("iso.md", b"x", "text/markdown")},
                headers={"User-Agent": "other-guest-1"},
            )
            fid = up.json()["fileId"]
            other.post(
                "/api/v1/jobs/",
                json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]},
                headers={"User-Agent": "other-guest-1"},
            )
            # original client should still see 0 (different identity)
            r = client.get("/api/v1/jobs/")
            assert r.json()["jobs"] == []


class TestJobsCreateValidation:
    def _upload(self, client, name="in.md", data=b"hello"):
        return client.post(
            "/api/v1/files/upload",
            files={"file": (name, data, "application/octet-stream")},
        ).json()["fileId"]

    def test_create_job_success_returns_conversion_info(self, client):
        fid = self._upload(client)
        r = client.post("/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "queued"
        assert body["conversion"]["id"] == "md-pdf"
        assert body["conversion"]["location"] == "server"
        assert "createdAt" in body

    def test_create_job_unsupported_conversion_422(self, client):
        fid = self._upload(client)
        r = client.post("/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "nonexistent"}]})
        assert r.status_code == 422

    def test_create_job_wrong_operation_422(self, client):
        fid = self._upload(client)
        r = client.post("/api/v1/jobs/", json={"tasks": [{"operation": "merge", "input": fid, "outputFormat": "pdf"}]})
        assert r.status_code == 422

    def test_create_job_empty_tasks_422(self, client):
        r = client.post("/api/v1/jobs/", json={"tasks": []})
        assert r.status_code == 422

    def test_get_job_after_create(self, client):
        fid = self._upload(client)
        job_id = client.post(
            "/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]}
        ).json()["id"]
        r = client.get(f"/api/v1/jobs/{job_id}")
        assert r.status_code == 200
        assert r.json()["id"] == job_id

    def test_get_job_not_found_404(self, client):
        r = client.get("/api/v1/jobs/nonexistent-id")
        assert r.status_code == 404

    def test_get_job_ownership_isolation(self, client):
        from fastapi.testclient import TestClient

        from app.main import create_app

        fid = self._upload(client)
        job_id = client.post(
            "/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]}
        ).json()["id"]
        # Different guest should not see the job (different UA => different identity)
        with TestClient(create_app(), headers={"User-Agent": "other-guest-2"}) as other:
            r = other.get(f"/api/v1/jobs/{job_id}", headers={"User-Agent": "other-guest-2"})
            assert r.status_code == 404


class TestJobsCancel:
    def _upload(self, client):
        return client.post(
            "/api/v1/files/upload",
            files={"file": ("a.md", b"x", "text/markdown")},
        ).json()["fileId"]

    def test_cancel_queued_job_succeeds(self, client, monkeypatch):
        # Prevent background task from racing: patch process_office_job to no-op
        import app.api.routes.jobs as jobs_module

        monkeypatch.setattr(jobs_module, "process_office_job", lambda *a, **kw: None)
        fid = self._upload(client)
        job_id = client.post(
            "/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]}
        ).json()["id"]
        r = client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert r.status_code == 200
        assert r.json()["cancelled"] is True
        assert r.json()["status"] == "cancelled"
        # verify persisted
        r2 = client.get(f"/api/v1/jobs/{job_id}")
        assert r2.json()["status"] == "cancelled"

    def test_cancel_already_cancelled_returns_false(self, client, monkeypatch):
        import app.api.routes.jobs as jobs_module

        monkeypatch.setattr(jobs_module, "process_office_job", lambda *a, **kw: None)
        fid = self._upload(client)
        job_id = client.post(
            "/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]}
        ).json()["id"]
        client.post(f"/api/v1/jobs/{job_id}/cancel")
        r = client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert r.json()["cancelled"] is False

    def test_cancel_missing_404(self, client):
        r = client.post("/api/v1/jobs/ghost/cancel")
        assert r.status_code == 404

    def test_cancel_other_guest_404(self, client):
        from fastapi.testclient import TestClient

        from app.main import create_app

        fid = self._upload(client)
        job_id = client.post(
            "/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]}
        ).json()["id"]
        with TestClient(create_app(), headers={"User-Agent": "other-guest-3"}) as other:
            r = other.post(f"/api/v1/jobs/{job_id}/cancel", headers={"User-Agent": "other-guest-3"})
            assert r.status_code == 404


class TestJobsEvents:
    def _upload(self, client):
        return client.post(
            "/api/v1/files/upload",
            files={"file": ("a.md", b"x", "text/markdown")},
        ).json()["fileId"]

    def test_events_returns_sse(self, client, monkeypatch):
        import app.api.routes.jobs as jobs_module

        monkeypatch.setattr(jobs_module, "process_office_job", lambda *a, **kw: None)
        fid = self._upload(client)
        job_id = client.post(
            "/api/v1/jobs/", json={"tasks": [{"operation": "convert", "input": fid, "outputFormat": "pdf"}]}
        ).json()["id"]
        # Cancel so job reaches terminal state; events should return quickly
        client.post(f"/api/v1/jobs/{job_id}/cancel")
        r = client.get(f"/api/v1/jobs/{job_id}/events")
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        assert "event: job" in r.text
        assert job_id in r.text

    def test_events_missing_404(self, client):
        r = client.get("/api/v1/jobs/ghost/events")
        assert r.status_code == 404

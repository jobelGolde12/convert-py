"""Benchmark harness: measures SQL query count + latency for key endpoints.

Usage: python scripts/benchmark.py
Run before and after optimizations; compare output.
"""

from __future__ import annotations

import os
import statistics
import tempfile
import time

_TMP = tempfile.mkdtemp(prefix="convert-bench-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/bench.db"
os.environ["LOCAL_STORAGE_ROOT"] = os.path.join(_TMP, "storage")
os.environ["REDIS_URL"] = "redis://127.0.0.1:1"  # unreachable -> memory fallback
os.environ["ENV"] = "development"

import logging  # noqa: E402

logging.disable(logging.INFO)  # keep benchmark output clean

from sqlalchemy import event  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.main import create_app  # noqa: E402

QUERY_COUNT = 0


def _before_cursor(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
    global QUERY_COUNT
    QUERY_COUNT += 1


event.listen(engine, "before_cursor_execute", _before_cursor)

MD = b"# Report\n\n- revenue is up\n- costs are down\n\nSee [docs](https://example.com)."


def timed(fn, repeats: int = 5) -> tuple[float, int]:
    """Run fn() repeatedly; return (median_ms, max_query_count)."""
    durations = []
    queries = 0
    global QUERY_COUNT
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        durations.append((time.perf_counter() - start) * 1000)
        queries = max(queries, QUERY_COUNT)
        QUERY_COUNT = 0
    return round(statistics.median(durations), 2), queries


def main() -> None:
    from fastapi.testclient import TestClient

    with TestClient(create_app()) as client:
        # Seed: upload + convert files so list_jobs has data (daily quota = 5).
        job_ids = []
        for i in range(4):
            up = client.post(
                "/api/v1/files/upload",
                files={"file": (f"report{i}.md", MD, "text/markdown")},
            )
            assert up.status_code == 200, up.text
            job = client.post(
                "/api/v1/jobs/",
                json={"tasks": [{"operation": "convert", "input": up.json()["fileId"], "outputFormat": "pdf"}]},
            )
            assert job.status_code == 200, job.text
            job_ids.append(job.json()["id"])

        results: dict[str, tuple[float, int]] = {}

        results["GET /healthz"] = timed(lambda: client.get("/healthz"))
        results["GET / (landing)"] = timed(lambda: client.get("/"))
        results["GET /convert"] = timed(lambda: client.get("/convert"))
        results["GET /api/v1/formats"] = timed(lambda: client.get("/api/v1/formats"))
        results["GET /api/v1/quota"] = timed(lambda: client.get("/api/v1/quota"))
        results["GET /api/v1/jobs/?limit=50"] = timed(
            lambda: client.get("/api/v1/jobs/", params={"limit": 50})
        )
        target = job_ids[0]
        results["GET /api/v1/jobs/{id}"] = timed(lambda: client.get(f"/api/v1/jobs/{target}"))
        results["POST /api/v1/files/upload"] = timed(
            lambda: client.post(
                "/api/v1/files/upload", files={"file": ("x.md", MD, "text/markdown")}
            ),
            repeats=3,
        )
        # Download of a completed output
        done = client.get(f"/api/v1/jobs/{job_ids[-1]}")
        outputs = done.json().get("outputs") or []
        if outputs:
            dl_url = outputs[0]["downloadUrl"]
            results["GET download (PDF)"] = timed(lambda: client.get(dl_url), repeats=3)
        else:
            print("NOTE: no completed outputs to benchmark download")

        print(f"{'Endpoint':32} {'median ms':>10} {'SQL queries':>12}")
        print("-" * 56)
        for name, (ms, q) in results.items():
            print(f"{name:32} {ms:>10.2f} {q:>12}")


if __name__ == "__main__":
    main()

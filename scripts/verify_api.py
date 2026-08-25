#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=10) as client:
        root = client.get("/")
        assert root.status_code == 200 and "Convert" in root.text, root.text[:200]
        assert "text/html" in root.headers.get("content-type", ""), root.headers

        for page in ("/convert", "/privacy", "/terms", "/healthz", "/robots.txt", "/sitemap.xml"):
            r = client.get(page)
            assert r.status_code == 200, (page, r.status_code)

        missing = client.get("/definitely-not-a-page")
        assert missing.status_code == 404, missing.status_code

        formats = client.get("/api/v1/formats")
        assert formats.status_code == 200 and "conversions" in formats.json(), formats.text

        quota = client.get("/api/v1/quota")
        assert quota.status_code == 200 and quota.json()["limit"] == 5, quota.text

    Path("/tmp/convert-py.verified").write_text("ok", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

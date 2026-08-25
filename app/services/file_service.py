from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from app.core.config import settings


def sign_payload(payload: bytes) -> str:
    secret = settings.upload_signing_secret or settings.upload_secret or "dev"
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def create_signed_upload(path: str, expires_in: int = 900) -> dict[str, Any]:
    expires_at = int(time.time()) + expires_in
    payload = f"upload:{path}:{expires_at}".encode("utf-8")
    signature = sign_payload(payload)
    return {
        "signedPath": path,
        "expiresAt": expires_at,
        "signature": signature,
    }


def verify_signed_upload(path: str, expires_at: int, signature: str) -> bool:
    payload = f"upload:{path}:{expires_at}".encode("utf-8")
    expected = sign_payload(payload)
    return hmac.compare_digest(expected, signature)


def file_extension_for(target: str) -> str:
    mapping = {
        "pdf": "pdf",
        "docx": "docx",
        "doc": "doc",
        "xlsx": "xlsx",
        "pptx": "pptx",
        "html": "html",
        "txt": "txt",
        "md": "md",
        "png": "png",
        "jpg": "jpg",
        "jpeg": "jpeg",
        "webp": "webp",
        "gif": "gif",
        "bmp": "bmp",
        "csv": "csv",
        "rtf": "rtf",
        "epub": "epub",
    }
    return mapping.get(target, target)


def mime_for(target: str) -> str:
    mapping = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "html": "text/html",
        "txt": "text/plain",
        "md": "text/markdown",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
        "bmp": "image/bmp",
    }
    return mapping.get(target, "application/octet-stream")


def content_disposition(filename: str) -> str:
    """Build a safe RFC 6266/5987 Content-Disposition value.

    Strips CR/LF and control characters (header injection), quotes a
    transliterated ASCII fallback, and provides an RFC 5987 filename* for
    non-ASCII names.
    """
    import unicodedata
    from urllib.parse import quote

    # Drop control characters including CR/LF.
    cleaned = "".join(ch for ch in filename if ord(ch) >= 32 and ch != "\x7f")

    fallback = (
        unicodedata.normalize("NFKD", cleaned)
        .encode("ascii", "ignore")
        .decode()
        .replace('"', "")
        .replace("\\", "")
        .strip()
        or "download"
    )

    if cleaned.isascii():
        safe = cleaned.replace('"', "").replace("\\", "").strip() or fallback
        return f'attachment; filename="{safe}"'

    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(cleaned)}"


def max_upload_bytes_for(source_format: str) -> int:
    """Actual server-side byte ceiling for a given detected source format."""
    from app.core.conversions_catalog import conversions_from

    mb = max((c.maxSizeMB for c in conversions_from(source_format)), default=25)
    return mb * 1024 * 1024

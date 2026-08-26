from __future__ import annotations


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

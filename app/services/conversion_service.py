from __future__ import annotations

import hashlib
import logging
import os
import subprocess
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import OfficeError

log = logging.getLogger(__name__)


class ConversionResult:
    def __init__(self, output_path: str, stdout: str, stderr: str):
        self.output_path = output_path
        self.stdout = stdout
        self.stderr = stderr


SOFFICE_FILTERS: dict[str, str] = {
    "pdf": "pdf",
    "docx": "docx:MS Word 2007 XML",
    "xlsx": "xlsx:Calc MS Excel 2007 XML",
    "pptx": "pptx:Impress MS PowerPoint 2007 XML",
    "html": "html:HTML (StarWriter)",
    "txt": "txt:Text (encoded):UTF8",
    "epub": "epub:EPUB",
}

# Error patterns in LibreOffice stderr that indicate a failed conversion even
# when the process exits with code 0.  LibreOffice sometimes writes error
# messages to stderr but still returns 0, which makes ``check=True`` useless
# for detecting these failures.
# Only match uppercase "Error:" which LibreOffice uses for actual failures.
# Lowercase "error:" is too broad and triggers on benign diagnostic lines.
_LO_SILENT_FAILURE_PATTERNS = (
    "Error:",
    "could not be loaded",
    "no export filter",
    "SfxBaseModel::impl_store",
    "Error Area:",
)


def _stderr_indicates_failure(stderr: str) -> bool:
    """Return *True* when stderr contains patterns that signal a failed conversion."""
    return any(pat in stderr for pat in _LO_SILENT_FAILURE_PATTERNS)


def soffice_filter_for(target: str) -> str:
    value = SOFFICE_FILTERS.get(target)
    if not value:
        raise OfficeError(f"Unsupported LibreOffice target: {target}", "UNSUPPORTED_FORMAT")
    return value


def convert_with_soffice(
    input_path: str,
    out_dir: str,
    target: str,
    *,
    profile_dir: str | None = None,
    timeout_ms: int | None = None,
) -> ConversionResult:
    timeout_ms = timeout_ms or settings.lo_timeout_ms
    profile_dir = profile_dir or os.path.join(
        settings.lo_profile_root, f"p-{os.getpid()}-{id(object())}"
    )
    os.makedirs(profile_dir, exist_ok=True)

    filter_name = soffice_filter_for(target)

    os.makedirs(out_dir, exist_ok=True)
    args = [
        "soffice",
        "--headless",
        "--norestore",
        "--nolockcheck",
        "--nologo",
        f"-env:UserInstallation=file://{profile_dir}",
        "--convert-to",
        filter_name,
        "--outdir",
        out_dir,
        input_path,
    ]

    log.info("Running: %s", " ".join(args))

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000,
            check=False,
        )
    except FileNotFoundError as exc:
        raise OfficeError("soffice not found on PATH", "ENGINE_UNAVAILABLE") from exc
    except subprocess.TimeoutExpired as exc:
        raise OfficeError(
            f"LibreOffice timed out after {round(timeout_ms/1000)}s", "TIMEOUT"
        ) from exc

    log.info("LibreOffice exited with code %d", proc.returncode)
    if proc.stdout.strip():
        log.info("LibreOffice stdout: %s", proc.stdout.strip()[:500])
    if proc.stderr.strip():
        log.warning("LibreOffice stderr: %s", proc.stderr.strip()[:1000])

    # LibreOffice may exit 0 but write errors to stderr.  Treat these as
    # failures so we surface the real error instead of silently producing no
    # output.
    if proc.returncode != 0 or _stderr_indicates_failure(proc.stderr):
        error_detail = proc.stderr.strip()[:500] or proc.stdout.strip()[:500]
        raise OfficeError(
            f"LibreOffice failed (exit {proc.returncode}): {error_detail}",
            "CONVERSION_FAILED",
        )

    base = Path(input_path).stem
    candidate = Path(out_dir) / f"{base}.{target}"
    if candidate.exists():
        log.info("Found expected output: %s", candidate)
        return ConversionResult(str(candidate), proc.stdout, proc.stderr)

    files = [p for p in Path(out_dir).iterdir() if p.is_file()]
    if not files:
        raise OfficeError("LibreOffice produced no output file", "CONVERSION_FAILED")
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    log.info("Falling back to most recent output: %s", files[0])
    return ConversionResult(str(files[0]), proc.stdout, proc.stderr)


def validate_output(target: str, data: bytes) -> None:
    if not data:
        raise OfficeError("Engine produced an empty output", "CONVERSION_FAILED")
    head = data[:4]
    if target == "pdf" and not head.startswith(b"%PDF"):
        raise OfficeError("Engine produced an invalid PDF", "CONVERSION_FAILED")
    if target in {"docx", "xlsx", "pptx"} and not head.startswith(b"PK"):
        raise OfficeError(f"Engine produced an invalid {target.upper()} file", "CONVERSION_FAILED")
    if target == "html":
        # Check the first 512 bytes for common HTML markers.
        head_512 = data[:512].lower()
        html_markers = (b"<!doctype", b"<html", b"<head", b"<body", b"<meta")
        if not any(m in head_512 for m in html_markers):
            raise OfficeError("Engine produced an invalid HTML file", "CONVERSION_FAILED")


# ---------------------------------------------------------------------------
# PDF text extraction helper (shared by fallback converters)
# ---------------------------------------------------------------------------
def _extract_text_from_pdf(input_path: str) -> str:
    """Extract text from a PDF using ``pdftotext`` with layout preservation."""
    import subprocess as _sp

    log.info("Extracting text from PDF with pdftotext: %s", input_path)
    try:
        result = _sp.run(
            ["pdftotext", "-layout", input_path, "-"],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
    except FileNotFoundError:
        raise OfficeError("pdftotext not found on PATH", "ENGINE_UNAVAILABLE")
    except _sp.TimeoutExpired:
        raise OfficeError("pdftotext timed out after 120s", "TIMEOUT")
    except _sp.CalledProcessError as exc:
        raise OfficeError(
            f"pdftotext failed (exit {exc.returncode}): {exc.stderr[:500]}",
            "CONVERSION_FAILED",
        )

    text = result.stdout
    if not text.strip():
        raise OfficeError(
            "PDF contains no extractable text (image-only PDF?)", "CONVERSION_FAILED"
        )
    return text


# ---------------------------------------------------------------------------
# Fallback conversion: PDF → DOCX via pdftotext + python-docx
# ---------------------------------------------------------------------------
# LibreOffice opens PDFs using the Draw application, which cannot export to
# Writer-based formats (DOCX).  When the primary soffice conversion fails for
# a PDF→DOCX path we fall back to extracting text with ``pdftotext`` and
# rebuilding a Word document with ``python-docx``.
# ---------------------------------------------------------------------------

def convert_pdf_to_docx_fallback(
    input_path: str,
    out_dir: str,
) -> ConversionResult:
    """Extract text from a PDF and create a DOCX using pdftotext + python-docx."""
    from docx import Document
    from docx.shared import Pt, Inches

    base = Path(input_path).stem
    out_path = Path(out_dir) / f"{base}.docx"
    os.makedirs(out_dir, exist_ok=True)

    text = _extract_text_from_pdf(input_path)

    # Build a DOCX from the extracted text
    log.info("Building DOCX from extracted text (%d chars)", len(text))
    doc = Document()

    # Set default font
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)

    # Set narrow margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    lines = text.split("\n")
    for line in lines:
        # Collapse excessive blank lines
        if not line.strip():
            continue
        doc.add_paragraph(line)

    doc.save(str(out_path))
    log.info("Fallback DOCX written to %s (%d bytes)", out_path, out_path.stat().st_size)

    return ConversionResult(str(out_path), "", "")


def convert_pdf_to_xlsx_fallback(
    input_path: str,
    out_dir: str,
) -> ConversionResult:
    """Extract text from a PDF and create an XLSX using pdftotext + openpyxl."""
    from openpyxl import Workbook

    base = Path(input_path).stem
    out_path = Path(out_dir) / f"{base}.xlsx"
    os.makedirs(out_dir, exist_ok=True)

    text = _extract_text_from_pdf(input_path)

    # Build an XLSX from the extracted text
    # NOTE: this is a plain-text reconstruction; tables and formatting are lost.
    log.info("Building XLSX from extracted text (%d chars)", len(text))
    wb = Workbook()
    ws = wb.active
    ws.title = "PDF Content"

    lines = text.split("\n")
    row_num = 1
    for line in lines:
        if not line.strip():
            continue
        ws.cell(row=row_num, column=1, value=line)
        row_num += 1

    # Column width tuned for typical extracted text (not a table layout).
    ws.column_dimensions["A"].width = 80

    wb.save(str(out_path))
    log.info("Fallback XLSX written to %s (%d bytes)", out_path, out_path.stat().st_size)

    return ConversionResult(str(out_path), "", "")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def markdown_to_html(md: str) -> str:
    import html as _html
    import re

    def esc(s: str) -> str:
        return _html.escape(s, quote=False)

    lines = md.replace("\r\n", "\n").split("\n")
    html_parts: list[str] = []
    in_list: str | None = None

    _link_re = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
    _bold_re = re.compile(r"\*\*(.+?)\*\*")
    _italic_re = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
    _code_re = re.compile(r"`([^`]+)`")

    def inline(s: str) -> str:
        # s is already escaped; build tags from escaped text so raw HTML never leaks.
        s = _code_re.sub(lambda m: f"<code>{m.group(1)}</code>", s)
        s = _bold_re.sub(lambda m: f"<strong>{m.group(1)}</strong>", s)
        s = _italic_re.sub(lambda m: f"<em>{m.group(1)}</em>", s)
        s = _link_re.sub(
            lambda m: f'<a href="{_html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', s
        )
        return s

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_parts.append(f"</{in_list}>")
            in_list = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_list()
            continue
        heading = line.split(" ", 1)
        if heading[0].startswith("#") and len(heading[0]) <= 3 and len(heading) > 1:
            close_list()
            level = len(heading[0])
            html_parts.append(f"<h{level}>{inline(esc(heading[1]))}</h{level}>")
            continue
        ul = line.split(" ", 1)
        if ul[0] in {"-", "*"} and len(ul) > 1:
            if in_list != "ul":
                close_list()
                html_parts.append("<ul>")
                in_list = "ul"
            html_parts.append(f"<li>{inline(esc(ul[1]))}</li>")
            continue
        close_list()
        html_parts.append(f"<p>{inline(esc(line))}</p>")
    close_list()

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8' /><style>"
        "body{font-family:Inter,'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:11pt;line-height:1.55;color:#171717;margin:2.2cm 2.4cm;}"
        "h1{font-size:22pt;font-weight:500;letter-spacing:-0.02em;margin:0 0 0.4em;}"
        "h2{font-size:15pt;font-weight:500;margin:1.2em 0 0.3em;}"
        "h3{font-size:12.5pt;font-weight:600;margin:1em 0 0.2em;}"
        "p{margin:0.5em 0;} ul,ol{margin:0.4em 0;padding-left:1.4em;} li{margin:0.15em 0;}"
        "blockquote{border-left:2px solid #C8102E;margin:0.6em 0;padding-left:1em;color:#6B6B6B;}"
        "code{background:#F7F7F5;padding:0.1em 0.3em;border-radius:2px;font-size:0.92em;}"
        "hr{border:none;border-top:1px solid #DCDCDC;margin:1.2em 0;}"
        "a{color:#C8102E;}"
        "</style></head><body>" + "\n".join(html_parts) + "</body></html>"
    )

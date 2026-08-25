from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import OfficeError


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
}


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
    filter_name = soffice_filter_for(target)

    os.makedirs(out_dir, exist_ok=True)
    args = [
        "soffice",
        "--headless",
        "--norestore",
        "--nolockcheck",
        "--nodefault",
        f"-env:UserInstallation=file://{profile_dir}",
        "--convert-to",
        filter_name,
        "--outdir",
        out_dir,
        input_path,
    ]

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000,
            check=True,
        )
    except FileNotFoundError as exc:
        raise OfficeError("soffice not found on PATH", "ENGINE_UNAVAILABLE") from exc
    except subprocess.TimeoutExpired as exc:
        raise OfficeError(
            f"LibreOffice timed out after {round(timeout_ms/1000)}s", "TIMEOUT"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise OfficeError(
            f"LibreOffice exited with code {exc.returncode}: {exc.stderr[:500]}",
            "CONVERSION_FAILED",
        ) from exc

    base = Path(input_path).stem
    out_ext = target if target not in {"html", "txt"} else target
    candidate = Path(out_dir) / f"{base}.{out_ext}"
    if candidate.exists():
        return ConversionResult(str(candidate), proc.stdout, proc.stderr)

    files = [p for p in Path(out_dir).iterdir() if p.is_file()]
    if not files:
        raise OfficeError("LibreOffice produced no output file", "CONVERSION_FAILED")
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return ConversionResult(str(files[0]), proc.stdout, proc.stderr)


def validate_output(target: str, data: bytes) -> None:
    if not data:
        raise OfficeError("Engine produced an empty output", "CONVERSION_FAILED")
    head = data[:4]
    if target == "pdf" and not head.startswith(b"%PDF"):
        raise OfficeError("Engine produced an invalid PDF", "CONVERSION_FAILED")
    if target in {"docx", "xlsx", "pptx"} and not head.startswith(b"PK"):
        raise OfficeError(f"Engine produced an invalid {target.upper()} file", "CONVERSION_FAILED")
    if target == "html" and head[:1] not in {b"<", b" "}:
        raise OfficeError("Engine produced an invalid HTML file", "CONVERSION_FAILED")


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

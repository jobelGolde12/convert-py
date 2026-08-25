from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FormatDef(BaseModel):
    format: str
    label: str
    extensions: list[str]
    mimes: list[str]
    group: str


FORMATS: list[FormatDef] = [
    FormatDef(
        format="pdf", label="PDF", extensions=["pdf"], mimes=["application/pdf"], group="document"
    ),
    FormatDef(
        format="docx",
        label="Word",
        extensions=["docx"],
        mimes=["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        group="document",
    ),
    FormatDef(
        format="doc",
        label="Word (legacy)",
        extensions=["doc"],
        mimes=["application/msword"],
        group="document",
    ),
    FormatDef(
        format="rtf",
        label="RTF",
        extensions=["rtf"],
        mimes=["application/rtf", "text/rtf"],
        group="document",
    ),
    FormatDef(
        format="pptx",
        label="PowerPoint",
        extensions=["pptx"],
        mimes=["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
        group="presentation",
    ),
    FormatDef(
        format="ppt",
        label="PowerPoint (legacy)",
        extensions=["ppt"],
        mimes=["application/vnd.ms-powerpoint"],
        group="presentation",
    ),
    FormatDef(
        format="xlsx",
        label="Excel",
        extensions=["xlsx"],
        mimes=["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        group="spreadsheet",
    ),
    FormatDef(
        format="xls",
        label="Excel (legacy)",
        extensions=["xls"],
        mimes=["application/vnd.ms-excel"],
        group="spreadsheet",
    ),
    FormatDef(
        format="csv", label="CSV", extensions=["csv"], mimes=["text/csv"], group="spreadsheet"
    ),
    FormatDef(format="txt", label="Text", extensions=["txt"], mimes=["text/plain"], group="text"),
    FormatDef(
        format="md",
        label="Markdown",
        extensions=["md", "markdown"],
        mimes=["text/markdown", "text/x-markdown"],
        group="text",
    ),
    FormatDef(
        format="html", label="HTML", extensions=["html", "htm"], mimes=["text/html"], group="web"
    ),
    FormatDef(
        format="epub",
        label="EPUB",
        extensions=["epub"],
        mimes=["application/epub+zip"],
        group="document",
    ),
    FormatDef(format="png", label="PNG", extensions=["png"], mimes=["image/png"], group="image"),
    FormatDef(
        format="jpg", label="JPEG", extensions=["jpg", "jpeg"], mimes=["image/jpeg"], group="image"
    ),
    FormatDef(
        format="webp", label="WebP", extensions=["webp"], mimes=["image/webp"], group="image"
    ),
    FormatDef(format="gif", label="GIF", extensions=["gif"], mimes=["image/gif"], group="image"),
    FormatDef(format="bmp", label="BMP", extensions=["bmp"], mimes=["image/bmp"], group="image"),
]


class ConversionDef(BaseModel):
    id: str
    from_: list[str]
    to: str
    engine: str
    location: str
    category: str
    label: str
    shortLabel: str
    maxSizeMB: int
    priceCredits: int
    description: str


CONVERSIONS: list[ConversionDef] = [
    ConversionDef(
        id="docx-pdf",
        from_=["docx", "doc"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="office-to-pdf",
        label="Word to PDF",
        shortLabel="Word → PDF",
        maxSizeMB=100,
        priceCredits=1,
        description="Convert Word documents to PDF with embedded fonts and stable layout.",
    ),
    ConversionDef(
        id="pptx-pdf",
        from_=["pptx", "ppt"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="office-to-pdf",
        label="PowerPoint to PDF",
        shortLabel="PowerPoint → PDF",
        maxSizeMB=100,
        priceCredits=1,
        description="Turn slide decks into print-ready PDFs, one slide per page.",
    ),
    ConversionDef(
        id="xlsx-pdf",
        from_=["xlsx", "xls"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="office-to-pdf",
        label="Excel to PDF",
        shortLabel="Excel → PDF",
        maxSizeMB=100,
        priceCredits=1,
        description="Spreadsheets to PDF with print areas and one sheet per page.",
    ),
    ConversionDef(
        id="csv-pdf",
        from_=["csv"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="office-to-pdf",
        label="CSV to PDF",
        shortLabel="CSV → PDF",
        maxSizeMB=25,
        priceCredits=1,
        description="CSV data rendered as a clean, print-ready table.",
    ),
    ConversionDef(
        id="rtf-pdf",
        from_=["rtf"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="office-to-pdf",
        label="RTF to PDF",
        shortLabel="RTF → PDF",
        maxSizeMB=25,
        priceCredits=1,
        description="Rich text format documents to PDF.",
    ),
    ConversionDef(
        id="epub-pdf",
        from_=["epub"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="office-to-pdf",
        label="EPUB to PDF",
        shortLabel="EPUB → PDF",
        maxSizeMB=50,
        priceCredits=1,
        description="eBooks to PDF for printing and sharing.",
    ),
    ConversionDef(
        id="pdf-docx",
        from_=["pdf"],
        to="docx",
        engine="libreoffice",
        location="server",
        category="pdf-to-office",
        label="PDF to Word",
        shortLabel="PDF → Word",
        maxSizeMB=100,
        priceCredits=2,
        description="Rebuild PDF text as an editable Word document. Best for text-based PDFs.",
    ),
    ConversionDef(
        id="pdf-xlsx",
        from_=["pdf"],
        to="xlsx",
        engine="libreoffice",
        location="server",
        category="pdf-to-office",
        label="PDF to Excel",
        shortLabel="PDF → Excel",
        maxSizeMB=100,
        priceCredits=2,
        description="Extract tables from PDFs into an editable spreadsheet.",
    ),
    ConversionDef(
        id="pdf-pptx",
        from_=["pdf"],
        to="pptx",
        engine="libreoffice",
        location="server",
        category="pdf-to-office",
        label="PDF to PowerPoint",
        shortLabel="PDF → PowerPoint",
        maxSizeMB=100,
        priceCredits=3,
        description="PDF pages into editable slides. Layout fidelity varies with complex designs.",
    ),
    ConversionDef(
        id="pptx-docx",
        from_=["pptx", "ppt"],
        to="docx",
        engine="libreoffice",
        location="server",
        category="office-to-office",
        label="PowerPoint to Word",
        shortLabel="PowerPoint → Word",
        maxSizeMB=100,
        priceCredits=2,
        description="Slide content into a Word outline you can edit.",
    ),
    ConversionDef(
        id="docx-xlsx",
        from_=["docx", "doc"],
        to="xlsx",
        engine="libreoffice",
        location="server",
        category="office-to-office",
        label="Word to Excel",
        shortLabel="Word → Excel",
        maxSizeMB=100,
        priceCredits=2,
        description="Word content into a spreadsheet. Best for tabular documents.",
    ),
    ConversionDef(
        id="csv-xlsx",
        from_=["csv"],
        to="xlsx",
        engine="libreoffice",
        location="server",
        category="office-to-office",
        label="CSV to Excel",
        shortLabel="CSV → Excel",
        maxSizeMB=25,
        priceCredits=1,
        description="CSV into a native .xlsx workbook.",
    ),
    ConversionDef(
        id="docx-html",
        from_=["docx", "doc"],
        to="html",
        engine="libreoffice",
        location="server",
        category="office-to-office",
        label="Word to HTML",
        shortLabel="Word → HTML",
        maxSizeMB=50,
        priceCredits=1,
        description="Word documents to clean, web-ready HTML.",
    ),
    ConversionDef(
        id="html-pdf",
        from_=["html", "htm"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="web",
        label="HTML to PDF",
        shortLabel="HTML → PDF",
        maxSizeMB=25,
        priceCredits=1,
        description="Web pages and HTML files to PDF, honoring inline CSS.",
    ),
    ConversionDef(
        id="md-pdf",
        from_=["md"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="web",
        label="Markdown to PDF",
        shortLabel="Markdown → PDF",
        maxSizeMB=10,
        priceCredits=1,
        description="Markdown rendered with clean editorial typography to PDF.",
    ),
    ConversionDef(
        id="txt-pdf",
        from_=["txt"],
        to="pdf",
        engine="libreoffice",
        location="server",
        category="web",
        label="Text to PDF",
        shortLabel="Text → PDF",
        maxSizeMB=10,
        priceCredits=1,
        description="Plain text to a tidy, printable PDF.",
    ),
    ConversionDef(
        id="pdf-merge",
        from_=["pdf"],
        to="pdf",
        engine="pdf-lib",
        location="client",
        category="pdf-tools",
        label="Merge PDF",
        shortLabel="Merge",
        maxSizeMB=200,
        priceCredits=1,
        description="Combine multiple PDFs in order. Runs on your device.",
    ),
    ConversionDef(
        id="pdf-split",
        from_=["pdf"],
        to="pdf",
        engine="pdf-lib",
        location="client",
        category="pdf-tools",
        label="Split PDF",
        shortLabel="Split",
        maxSizeMB=100,
        priceCredits=1,
        description="Extract page ranges as separate PDFs. Runs on your device.",
    ),
    ConversionDef(
        id="pdf-rotate",
        from_=["pdf"],
        to="pdf",
        engine="pdf-lib",
        location="client",
        category="pdf-tools",
        label="Rotate PDF",
        shortLabel="Rotate",
        maxSizeMB=100,
        priceCredits=1,
        description="Rotate all or selected pages 90/180/270 degrees. Runs on your device.",
    ),
    ConversionDef(
        id="pdf-watermark",
        from_=["pdf"],
        to="pdf",
        engine="pdf-lib",
        location="client",
        category="pdf-tools",
        label="Watermark PDF",
        shortLabel="Watermark",
        maxSizeMB=100,
        priceCredits=1,
        description="Add a text watermark to every page. Runs on your device.",
    ),
    ConversionDef(
        id="pdf-compress",
        from_=["pdf"],
        to="pdf",
        engine="pdf-lib",
        location="client",
        category="pdf-tools",
        label="Compress PDF",
        shortLabel="Compress",
        maxSizeMB=100,
        priceCredits=1,
        description="Reduce PDF size. High level re-encodes pages; lossless strips redundancy. Runs on your device.",
    ),
    ConversionDef(
        id="pdf-txt",
        from_=["pdf"],
        to="txt",
        engine="pdfjs",
        location="client",
        category="text",
        label="PDF to Text",
        shortLabel="PDF → Text",
        maxSizeMB=50,
        priceCredits=1,
        description="Extract text from PDFs. Runs on your device.",
    ),
    ConversionDef(
        id="pdf-md",
        from_=["pdf"],
        to="md",
        engine="pdfjs",
        location="client",
        category="text",
        label="PDF to Markdown",
        shortLabel="PDF → Markdown",
        maxSizeMB=50,
        priceCredits=1,
        description="PDF text as Markdown. Runs on your device.",
    ),
    ConversionDef(
        id="pdf-image",
        from_=["pdf"],
        to="png",
        engine="pdfjs",
        location="client",
        category="image",
        label="PDF to Image",
        shortLabel="PDF → Image",
        maxSizeMB=50,
        priceCredits=1,
        description="Render PDF pages as PNG images. Runs on your device.",
    ),
    ConversionDef(
        id="image-pdf",
        from_=["png", "jpg", "jpeg", "webp", "gif", "bmp"],
        to="pdf",
        engine="client",
        location="client",
        category="image",
        label="Image to PDF",
        shortLabel="Image → PDF",
        maxSizeMB=50,
        priceCredits=1,
        description="Images into a single PDF, one per page. Runs on your device.",
    ),
]


_ext_to_format: dict[str, str] = {}
_mime_to_format: dict[str, str] = {}
for f in FORMATS:
    for ext in f.extensions:
        _ext_to_format[ext] = f.format
    for m in f.mimes:
        _mime_to_format[m.lower()] = f.format

_conversion_index: dict[tuple[str, str], ConversionDef] = {}
for c in CONVERSIONS:
    for src in c.from_:
        _conversion_index[(src, c.to)] = c


def detect_format(filename: str, mime: str | None) -> str | None:
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in _ext_to_format:
            return _ext_to_format[ext]
    if mime and mime.lower() in _mime_to_format:
        return _mime_to_format[mime.lower()]
    return None


def conversions_from(source: str) -> list[ConversionDef]:
    return [c for c in CONVERSIONS if source in c.from_]


def find_conversion(source: str, target: str) -> ConversionDef | None:
    return _conversion_index.get((source, target))


def extension_for(target: str) -> str:
    for f in FORMATS:
        if f.format == target:
            return f.extensions[0]
    return target


def public_catalog() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in CONVERSIONS:
        item = c.model_dump()
        item["from"] = item.pop("from_")
        out.append(item)
    return out

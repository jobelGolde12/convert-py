from __future__ import annotations

from app.core.conversions_catalog import (
    CONVERSIONS,
    FORMATS,
    conversions_from,
    detect_format,
    extension_for,
    find_conversion,
    public_catalog,
)
from app.services.file_service import content_disposition, max_upload_bytes_for, mime_for


class TestMimeFor:
    def test_known_mimes(self):
        assert mime_for("pdf") == "application/pdf"
        assert mime_for("docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert mime_for("xlsx") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert mime_for("html") == "text/html"
        assert mime_for("txt") == "text/plain"
        assert mime_for("png") == "image/png"

    def test_unknown_returns_octet_stream(self):
        assert mime_for("xyz_unknown") == "application/octet-stream"
        assert mime_for("") == "application/octet-stream"


class TestContentDispositionExtra:
    def test_backslash_stripped(self):
        header = content_disposition("a\\b.pdf")
        assert "\\" not in header

    def test_control_chars_stripped(self):
        header = content_disposition("a\x00\x1fb.pdf")
        assert "\x00" not in header

    def test_empty_string_fallback(self):
        header = content_disposition("")
        assert 'filename="download"' in header

    def test_only_control_chars_fallback(self):
        header = content_disposition("\x01\x02\x03")
        assert "download" in header

    def test_long_unicode(self):
        header = content_disposition("🦄🎉.pdf")
        assert "filename*=" in header

    def test_ascii_with_spaces(self):
        header = content_disposition("my report (1).pdf")
        assert 'filename="my report (1).pdf"' in header


class TestMaxUploadBytesFor:
    def test_known_format(self):
        # pdf has maxSizeMB=100 in some conversion, 200 in merge – max is 200
        size = max_upload_bytes_for("pdf")
        assert size == 200 * 1024 * 1024

    def test_md_limit(self):
        # md only appears in md-pdf (10) and md-html (10) -> max 10
        assert max_upload_bytes_for("md") == 10 * 1024 * 1024

    def test_unknown_format_default(self):
        assert max_upload_bytes_for("nonexistent_format_xyz") == 25 * 1024 * 1024

    def test_docx_limit(self):
        assert max_upload_bytes_for("docx") == 100 * 1024 * 1024


class TestDetectFormatEdgeCases:
    def test_no_extension_no_mime(self):
        assert detect_format("noext", None) is None

    def test_unknown_extension_falls_back_to_mime(self):
        assert detect_format("file.unknown_ext", "application/pdf") == "pdf"

    def test_unknown_both_returns_none(self):
        assert detect_format("file.unknown_ext", "application/x-unknown") is None

    def test_case_insensitive_extension(self):
        assert detect_format("FILE.PDF", None) == "pdf"
        assert detect_format("file.Docx", None) == "docx"

    def test_mime_case_insensitive(self):
        assert detect_format("blob", "Application/PDF") == "pdf"
        assert detect_format("blob", "TEXT/MARKDOWN") == "md"

    def test_dot_in_filename_uses_last_segment(self):
        assert detect_format("archive.tar.pdf", None) == "pdf"
        assert detect_format("my.file.docx", None) == "docx"

    def test_empty_filename(self):
        assert detect_format("", "application/pdf") == "pdf"
        assert detect_format("", None) is None

    def test_markdown_secondary_extension(self):
        assert detect_format("notes.markdown", None) == "md"

    def test_html_htm_extension(self):
        assert detect_format("page.htm", None) == "html"
        assert detect_format("page.html", None) == "html"


class TestFindConversion:
    def test_known_server_conversion(self):
        c = find_conversion("docx", "pdf")
        assert c is not None
        assert c.location == "server"

    def test_client_only_conversion_found(self):
        c = find_conversion("pdf", "pdf")
        assert c is not None
        # pdf->pdf is merge via pdf-lib on client
        assert c.location == "client"

    def test_nonexistent_conversion_returns_none(self):
        assert find_conversion("pdf", "nonexistent") is None
        assert find_conversion("unknown", "pdf") is None
        assert find_conversion("", "") is None

    def test_md_to_pdf(self):
        c = find_conversion("md", "pdf")
        assert c is not None
        assert c.id == "md-pdf"

    def test_image_to_pdf(self):
        c = find_conversion("png", "pdf")
        assert c is not None
        assert c.id == "image-pdf"


class TestExtensionFor:
    def test_known(self):
        assert extension_for("pdf") == "pdf"
        assert extension_for("docx") == "docx"

    def test_unknown_returns_target(self):
        assert extension_for("nonexistent") == "nonexistent"

    def test_image_formats(self):
        assert extension_for("png") == "png"
        assert extension_for("jpg") == "jpg"


class TestConversionsFrom:
    def test_returns_multiple(self):
        results = conversions_from("pdf")
        assert len(results) >= 5
        ids = {c.id for c in results}
        assert "pdf-docx" in ids

    def test_unknown_source_empty(self):
        assert conversions_from("nonexistent_xyz") == []

    def test_md_source(self):
        results = conversions_from("md")
        assert len(results) == 2  # md-pdf, md-html
        ids = {c.id for c in results}
        assert ids == {"md-pdf", "md-html"}


class TestPublicCatalog:
    def test_uses_from_not_from_underscore(self):
        catalog = public_catalog()
        for item in catalog:
            assert "from" in item
            assert "from_" not in item

    def test_catalog_length_matches_conversions(self):
        assert len(public_catalog()) == len(CONVERSIONS)

    def test_catalog_has_required_keys(self):
        for item in public_catalog():
            assert "id" in item
            assert "to" in item
            assert "engine" in item
            assert "location" in item

    def test_catalog_sorted_categories_present(self):
        catalog = public_catalog()
        categories = {c["category"] for c in catalog}
        assert "office-to-pdf" in categories
        assert "pdf-tools" in categories

    def test_formats_have_groups(self):
        groups = {f.group for f in FORMATS}
        assert "document" in groups
        assert "spreadsheet" in groups
        assert "image" in groups

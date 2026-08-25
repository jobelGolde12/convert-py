from __future__ import annotations

from app.core.conversions_catalog import detect_format, extension_for, find_conversion
from app.services.conversion_service import markdown_to_html
from app.services.file_service import content_disposition


class TestMarkdownToHtml:
    def test_escapes_html_injection(self):
        out = markdown_to_html('<script>alert("x")</script>')
        assert "<script>" not in out.replace("<h1>", "").replace("</h1>", "")
        assert "&lt;script&gt;" in out

    def test_escapes_angle_brackets_inline(self):
        out = markdown_to_html("a < b and x > y")
        assert "a &lt; b and x &gt; y" in out

    def test_bold_italic_code(self):
        out = markdown_to_html("**bold** and *em* and `code`")
        assert "<strong>bold</strong>" in out
        assert "<em>em</em>" in out
        assert "<code>code</code>" in out

    def test_link_rendering(self):
        out = markdown_to_html("[docs](https://example.com)")
        assert '<a href="https://example.com">docs</a>' in out

    def test_headings_and_lists(self):
        import re

        out = markdown_to_html("# H1\n## H2\n### H3\n\n- one\n- two\n")
        assert "<h1>H1</h1>" in out
        assert "<h2>H2</h2>" in out
        assert "<h3>H3</h3>" in out
        compact = re.sub(r"\s+", "", out)
        assert "<ul><li>one</li><li>two</li></ul>" in compact

    def test_document_skeleton(self):
        out = markdown_to_html("hi")
        assert out.startswith("<!DOCTYPE html>")
        assert "</html>" in out


class TestCatalog:
    def test_detect_by_extension(self):
        assert detect_format("file.docx", None) == "docx"
        assert detect_format("FILE.PDF", None) == "pdf"
        assert detect_format("notes.markdown", None) == "md"
        assert detect_format("noext", None) is None

    def test_detect_by_mime(self):
        assert detect_format("blob", "application/pdf") == "pdf"

    def test_find_conversion(self):
        c = find_conversion("docx", "pdf")
        assert c and c.engine == "libreoffice" and c.location == "server"

    def test_extension_for(self):
        assert extension_for("pdf") == "pdf"


class TestContentDisposition:
    def test_ascii_quoted(self):
        assert content_disposition("report.pdf") == 'attachment; filename="report.pdf"'

    def test_crlf_stripped(self):
        header = content_disposition("a\r\nSet-Cookie: x=1.pdf")
        assert "\r" not in header and "\n" not in header

    def test_quotes_removed(self):
        assert content_disposition('we"ird.txt') == 'attachment; filename="weird.txt"'

    def test_unicode_rfc5987(self):
        header = content_disposition("résumé.pdf")
        assert "filename*=UTF-8''r%C3%A9sum%C3%A9.pdf" in header

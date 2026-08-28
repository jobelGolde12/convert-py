from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import OfficeError
from app.services.conversion_service import (
    _extract_text_from_pdf,
    _stderr_indicates_failure,
    convert_pdf_to_docx_fallback,
    convert_pdf_to_xlsx_fallback,
    markdown_to_html,
    sha256,
    soffice_filter_for,
    validate_output,
)


class TestSha256:
    def test_known_hash(self):
        assert sha256(b"hello") == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_empty_bytes(self):
        assert sha256(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_deterministic(self):
        assert sha256(b"foo") == sha256(b"foo")
        assert sha256(b"foo") != sha256(b"bar")


class TestSofficeFilterFor:
    def test_known_targets(self):
        assert soffice_filter_for("pdf") == "pdf"
        assert soffice_filter_for("docx") == "docx:MS Word 2007 XML"
        assert soffice_filter_for("xlsx") == "xlsx:Calc MS Excel 2007 XML"
        assert soffice_filter_for("html") == "html:HTML (StarWriter)"
        assert soffice_filter_for("txt") == "txt:Text (encoded):UTF8"

    def test_unsupported_target(self):
        with pytest.raises(OfficeError) as exc:
            soffice_filter_for("png")
        assert exc.value.code == "UNSUPPORTED_FORMAT"

    def test_empty_target(self):
        with pytest.raises(OfficeError):
            soffice_filter_for("")


class TestValidateOutput:
    def test_empty_data_fails(self):
        with pytest.raises(OfficeError, match="empty"):
            validate_output("pdf", b"")

    def test_valid_pdf(self):
        validate_output("pdf", b"%PDF-1.4 fake")

    def test_invalid_pdf(self):
        with pytest.raises(OfficeError, match="invalid PDF"):
            validate_output("pdf", b"not a pdf")

    def test_valid_docx(self):
        validate_output("docx", b"PK\x03\x04 fake zip")

    def test_invalid_docx(self):
        with pytest.raises(OfficeError, match="invalid DOCX"):
            validate_output("docx", b"not zip")

    def test_valid_xlsx(self):
        validate_output("xlsx", b"PK fake")

    def test_invalid_xlsx(self):
        with pytest.raises(OfficeError):
            validate_output("xlsx", b"BAD")

    def test_valid_pptx(self):
        validate_output("pptx", b"PK fake")

    def test_valid_html(self):
        validate_output("html", b"<html>hi</html>")
        validate_output("html", b" <html>")

    def test_invalid_html(self):
        with pytest.raises(OfficeError):
            validate_output("html", b"not html at all!!!".ljust(4, b"x"))

    def test_unknown_target_no_validation(self):
        # epub etc: validate_output only checks pdf/docx/xlsx/pptx/html
        validate_output("epub", b"anything")
        validate_output("txt", b"hello world")


class TestStderrIndicatesFailure:
    def test_detects_error_patterns(self):
        assert _stderr_indicates_failure("Error: something broke") is True
        assert _stderr_indicates_failure("could not be loaded") is True
        assert _stderr_indicates_failure("no export filter found") is True
        assert _stderr_indicates_failure("SfxBaseModel::impl_store failed") is True
        assert _stderr_indicates_failure("Error Area: foo") is True

    def test_clean_stderr_not_failure(self):
        assert _stderr_indicates_failure("") is False
        assert _stderr_indicates_failure("convert /tmp/input.html -> /tmp/out.pdf") is False
        assert _stderr_indicates_failure("LibreOffice 7.6") is False

    def test_lowercase_error_not_triggered(self):
        # Lowercase "error:" should NOT trigger (was removed as overly broad)
        assert _stderr_indicates_failure("info: error category loaded") is False
        assert _stderr_indicates_failure("Warning: some error: info") is False


class TestConvertWithSoffice:
    def test_soffice_not_found(self, tmp_path):
        inp = tmp_path / "in.html"
        inp.write_text("<html>hi</html>")
        out = str(tmp_path / "out")
        with patch("app.services.conversion_service.subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(OfficeError) as exc:
                from app.services.conversion_service import convert_with_soffice

                convert_with_soffice(str(inp), out, "pdf")
            assert exc.value.code == "ENGINE_UNAVAILABLE"

    def test_timeout(self, tmp_path):
        inp = tmp_path / "in.html"
        inp.write_text("<html>hi</html>")
        out = str(tmp_path / "out")
        with patch(
            "app.services.conversion_service.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="soffice", timeout=1),
        ):
            with pytest.raises(OfficeError) as exc:
                from app.services.conversion_service import convert_with_soffice

                convert_with_soffice(str(inp), out, "pdf")
            assert exc.value.code == "TIMEOUT"

    def test_nonzero_exit(self, tmp_path):
        inp = tmp_path / "in.html"
        inp.write_text("<html>hi</html>")
        out = str(tmp_path / "out")
        mock_proc = MagicMock(returncode=1, stdout="", stderr="Error: failed")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_proc):
            with pytest.raises(OfficeError) as exc:
                from app.services.conversion_service import convert_with_soffice

                convert_with_soffice(str(inp), out, "pdf")
            assert exc.value.code == "CONVERSION_FAILED"

    def test_stderr_silent_failure_triggers_error(self, tmp_path):
        inp = tmp_path / "in.html"
        inp.write_text("<html>hi</html>")
        out = str(tmp_path / "out")
        mock_proc = MagicMock(returncode=0, stdout="", stderr="Error: could not be loaded")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_proc):
            with pytest.raises(OfficeError):
                from app.services.conversion_service import convert_with_soffice

                convert_with_soffice(str(inp), out, "pdf")

    def test_success_finds_expected_output(self, tmp_path):
        inp = tmp_path / "input.html"
        inp.write_text("<html>hi</html>")
        out_dir = str(tmp_path / "out")
        mock_proc = MagicMock(returncode=0, stdout="convert", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_proc):
            # pre-create expected output file
            import os

            os.makedirs(out_dir, exist_ok=True)
            expected = tmp_path / "out" / "input.pdf"
            expected.write_bytes(b"%PDF fake")
            from app.services.conversion_service import convert_with_soffice

            result = convert_with_soffice(str(inp), out_dir, "pdf")
            assert result.output_path == str(expected)

    def test_success_fallback_to_most_recent(self, tmp_path):
        inp = tmp_path / "input.html"
        inp.write_text("<html>hi</html>")
        out_dir = str(tmp_path / "out")
        mock_proc = MagicMock(returncode=0, stdout="", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_proc):
            import os
            import time

            os.makedirs(out_dir, exist_ok=True)
            # LibreOffice may name output differently; fallback picks most recent file
            fallback = tmp_path / "out" / "something_else.pdf"
            fallback.write_bytes(b"%PDF fallback")
            # ensure mtime ordering
            time.sleep(0.01)
            from app.services.conversion_service import convert_with_soffice

            result = convert_with_soffice(str(inp), out_dir, "pdf")
            assert result.output_path == str(fallback)

    def test_no_output_file_raises(self, tmp_path):
        inp = tmp_path / "input.html"
        inp.write_text("<html>hi</html>")
        out_dir = str(tmp_path / "out")
        mock_proc = MagicMock(returncode=0, stdout="", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_proc):
            import os

            os.makedirs(out_dir, exist_ok=True)
            from app.services.conversion_service import convert_with_soffice

            with pytest.raises(OfficeError, match="no output"):
                convert_with_soffice(str(inp), out_dir, "pdf")


class TestMarkdownToHtmlEdgeCases:
    def test_empty_input(self):
        out = markdown_to_html("")
        assert "<!DOCTYPE html>" in out
        assert "</html>" in out

    def test_only_blank_lines(self):
        out = markdown_to_html("\n\n\n")
        assert "<!DOCTYPE html>" in out

    def test_crlf_normalization(self):
        out = markdown_to_html("# Title\r\n\r\nParagraph\r\n")
        assert "<h1>Title</h1>" in out
        assert "<p>Paragraph</p>" in out

    def test_multiple_paragraphs(self):
        out = markdown_to_html("para one\n\npara two")
        assert out.count("<p>") == 2

    def test_list_then_paragraph(self):
        out = markdown_to_html("- a\n- b\n\nNext paragraph")
        assert "<ul>" in out
        assert "<p>Next paragraph</p>" in out

    def test_ordered_list_not_supported_as_unordered(self):
        # Only "- " and "* " trigger lists; numeric lists become paragraphs
        out = markdown_to_html("1. first\n2. second")
        assert "<p>1. first</p>" in out

    def test_asterisk_list(self):
        out = markdown_to_html("* item one\n* item two")
        assert "<li>item one</li>" in out

    def test_html_injection_in_heading(self):
        out = markdown_to_html("# <script>alert(1)</script>")
        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    def test_code_inside_bold(self):
        out = markdown_to_html("**bold `code` inside**")
        # bold wraps but code is processed first, so code tag should appear
        assert "<code>code</code>" in out

    def test_link_with_special_chars(self):
        out = markdown_to_html("[a & b](https://example.com?a=1&b=2)")
        # URL is escaped via html.escape, so & becomes &amp; (double-escape from prior esc is expected)
        assert "https://example.com?a=1" in out
        assert "&amp;" in out
        assert 'href="' in out

    def test_inline_escaping_preserves_text(self):
        out = markdown_to_html("5 < 10 and 10 > 5")
        assert "5 &lt; 10 and 10 &gt; 5" in out

    def test_empty_link_text(self):
        # Edge: empty link text still produces anchor (regex allows it but [^\]]+ requires at least one char)
        out = markdown_to_html("[](https://example.com)")
        # Should NOT produce a link because [^\]]+ requires at least one char
        assert "<a href" not in out


class TestExtractTextFromPdf:
    def test_extracts_text(self, tmp_path):
        # Mock pdftotext to return known text
        mock_result = MagicMock(stdout="Hello from PDF\nLine 2", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_result):
            text = _extract_text_from_pdf("/fake/input.pdf")
        assert text == "Hello from PDF\nLine 2"

    def test_empty_text_raises(self, tmp_path):
        mock_result = MagicMock(stdout="   ", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_result):
            with pytest.raises(OfficeError, match="no extractable text"):
                _extract_text_from_pdf("/fake/empty.pdf")

    def test_pdftotext_not_found(self):
        with patch("app.services.conversion_service.subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(OfficeError, match="pdftotext not found"):
                _extract_text_from_pdf("/fake/input.pdf")

    def test_pdftotext_timeout(self):
        with patch(
            "app.services.conversion_service.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="pdftotext", timeout=120),
        ):
            with pytest.raises(OfficeError, match="timed out"):
                _extract_text_from_pdf("/fake/input.pdf")

    def test_pdftotext_nonzero_exit(self):
        exc = subprocess.CalledProcessError(1, "pdftotext", stderr="bad pdf")
        with patch("app.services.conversion_service.subprocess.run", side_effect=exc):
            with pytest.raises(OfficeError, match="pdftotext failed"):
                _extract_text_from_pdf("/fake/input.pdf")


class TestConvertPdfToDocxFallback:
    def test_produces_valid_docx(self, tmp_path):
        # Mock pdftotext to return text, then run the actual docx creation
        mock_result = MagicMock(stdout="Hello World\nSecond line", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_result):
            result = convert_pdf_to_docx_fallback("/fake/input.pdf", str(tmp_path / "out"))
        assert result.output_path.endswith(".docx")
        # Verify the output is a valid ZIP (docx is a zip)
        with open(result.output_path, "rb") as f:
            assert f.read(2) == b"PK"

    def test_empty_pdf_raises(self, tmp_path):
        mock_result = MagicMock(stdout="   ", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_result):
            with pytest.raises(OfficeError, match="no extractable text"):
                convert_pdf_to_docx_fallback("/fake/empty.pdf", str(tmp_path / "out"))


class TestConvertPdfToXlsxFallback:
    def test_produces_valid_xlsx(self, tmp_path):
        mock_result = MagicMock(stdout="Col1\tCol2\nA\tB", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_result):
            result = convert_pdf_to_xlsx_fallback("/fake/input.pdf", str(tmp_path / "out"))
        assert result.output_path.endswith(".xlsx")
        # Verify the output is a valid ZIP (xlsx is a zip)
        with open(result.output_path, "rb") as f:
            assert f.read(2) == b"PK"

    def test_empty_pdf_raises(self, tmp_path):
        mock_result = MagicMock(stdout="\n\n", stderr="")
        with patch("app.services.conversion_service.subprocess.run", return_value=mock_result):
            with pytest.raises(OfficeError, match="no extractable text"):
                convert_pdf_to_xlsx_fallback("/fake/empty.pdf", str(tmp_path / "out"))

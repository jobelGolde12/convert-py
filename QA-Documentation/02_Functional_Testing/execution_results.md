# Functional Test Execution Results

## Summary

- **Total Tests Executed**: 43 (pytest) + 13 (page tests) + 17 (API tests) + 6 (unit tests) + 7 (integration)
- **Passed**: 43
- **Failed**: 0
- **Blocked**: 0

## Detailed Results

| Test ID | Actual Result | Status | Evidence | Notes |
|---------|--------------|--------|----------|-------|
| TC-PAGE-001 | 200, HTML with Convert, canonical, OG, JSON-LD, aria-label="Primary", Skip to content | PASS | test_home_renders_html | |
| TC-PAGE-002 | 200, contains data-catalog, "Word to PDF", "from" (not "from_") | PASS | test_convert_page_embeds_catalog | |
| TC-PAGE-003 | 200, contains "Privacy" | PASS | test_privacy_page | |
| TC-PAGE-004 | 200, contains "Terms of use" | PASS | test_terms_page | |
| TC-PAGE-005 | 404, HTML with "404" | PASS | test_unknown_page_returns_404_html | |
| TC-PAGE-006 | 200, {"status": "ok"} | PASS | test_healthz | |
| TC-PAGE-007 | 200, contains "Sitemap:" and "Disallow: /api/" | PASS | test_robots_txt | |
| TC-PAGE-008 | 200, contains urlset and /convert | PASS | test_sitemap_xml | |
| TC-PAGE-009 | 200, svg content-type | PASS | test_favicon_served | |
| TC-PAGE-010 | nosniff, DENY, strict-origin-when-cross-origin | PASS | test_security_headers | |
| TC-UPLOAD-001 | 200, fileId, filename, sizeBytes, status=ready | PASS | test_upload_and_fetch | |
| TC-UPLOAD-002 | 200, content matches, filename="hi.txt" | PASS | test_download_roundtrip | |
| TC-UPLOAD-003 | 415 for .exe file | PASS | test_unsupported_extension_415 | |
| TC-UPLOAD-004 | 422 for empty upload | PASS | test_no_file_422 | |
| TC-UPLOAD-005 | 413, maxSizeMB=10 for 11MB .md | PASS | test_oversize_stream_rejected_413 | |
| TC-UPLOAD-006 | 404 for nonexistent file | PASS | test_missing_file_after_upload_404 | |
| TC-UPLOAD-007 | No CRLF, proper RFC 5987 for unicode | PASS | test_content_disposition_sanitized | |
| TC-JOB-001 | 404 for missing input | PASS | test_job_for_missing_input_404 | |
| TC-JOB-002 | 422, "browser" in response | PASS | test_client_only_conversion_rejected_422 | |
| TC-JOB-003 | 422 for invalid body | PASS | test_invalid_body_422 | |
| TC-JOB-004 | 404 for nonexistent job | PASS | test_cancel_missing_job_404 | |
| TC-JOB-005 | 200, empty jobs array | PASS | test_jobs_list_empty_for_new_guest | |
| TC-JOB-006 | 200, status=done, progress=100, valid PDF (%PDF header) | PASS | test_markdown_to_pdf_end_to_end | Requires LibreOffice |
| TC-RL-001 | 200, limit=5, remaining=5, resetsAt | PASS | test_quota_shape | |
| TC-RL-002 | HttpOnly, SameSite=lax in Set-Cookie | PASS | test_guest_cookie_is_set_httponly | |
| TC-RL-003 | 429 appears after 3 requests | PASS | test_rate_limit_kicks_in | |
| TC-UI-001 | id="theme-toggle" present | PASS | test_theme_toggle_and_mobile_nav_present | |
| TC-UI-002 | id="menu-toggle", id="mobile-nav" present | PASS | test_theme_toggle_and_mobile_nav_present | |
| TC-UI-003 | "Skip to content" present | PASS | test_home_renders_html | |

## Unit Test Results

| Test ID | Actual Result | Status | Evidence | Notes |
|---------|--------------|--------|----------|-------|
| TC-UNIT-001 | HTML injection escaped, &lt;script&gt; present | PASS | test_escapes_html_injection | |
| TC-UNIT-002 | "a &lt; b and x &gt; y" present | PASS | test_escapes_angle_brackets_inline | |
| TC-UNIT-003 | strong, em, code tags present | PASS | test_bold_italic_code | |
| TC-UNIT-004 | Link rendered with href | PASS | test_link_rendering | |
| TC-UNIT-005 | h1, h2, h3, ul, li present | PASS | test_headings_and_lists | |
| TC-UNIT-006 | Starts with DOCTYPE, contains /html | PASS | test_document_skeleton | |
| TC-UNIT-007 | Extension detection works | PASS | test_detect_by_extension | |
| TC-UNIT-008 | MIME detection works | PASS | test_detect_by_mime | |
| TC-UNIT-009 | Conversion found for docx→pdf | PASS | test_find_conversion | |
| TC-UNIT-010 | extension_for returns correct value | PASS | test_extension_for | |
| TC-UNIT-011 | ASCII filename quoted correctly | PASS | test_ascii_quoted | |
| TC-UNIT-012 | CRLF stripped from header | PASS | test_crlf_stripped | |
| TC-UNIT-013 | Quotes removed from filename | PASS | test_quotes_removed | |
| TC-UNIT-014 | Unicode encoded via RFC 5987 | PASS | test_unicode_rfc5987 | |

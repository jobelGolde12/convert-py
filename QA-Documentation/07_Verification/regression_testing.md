# Regression Testing

## Test Execution

All 43 tests executed after implementing all fixes. Results below.

| Area | Test | Result | Notes |
|------|------|--------|-------|
| Page Rendering | test_home_renders_html | PASS | Home page renders correctly |
| Page Rendering | test_convert_page_embeds_catalog | PASS | Convert page with catalog data |
| Page Rendering | test_privacy_page | PASS | Privacy page renders |
| Page Rendering | test_terms_page | PASS | Terms page renders |
| Page Rendering | test_unknown_page_returns_404_html | PASS | Custom 404 page works |
| Page Rendering | test_unknown_api_path_returns_404_json | PASS | API 404 returns JSON |
| Page Rendering | test_healthz | PASS | Health check works |
| Page Rendering | test_security_headers | PASS | Security headers present |
| Page Rendering | test_robots_txt | PASS | Robots.txt served |
| Page Rendering | test_sitemap_xml | PASS | Sitemap XML valid |
| Page Rendering | test_favicon_served | PASS | Favicon served |
| Page Rendering | test_theme_toggle_and_mobile_nav_present | PASS | UI elements present |
| File Upload | test_upload_and_fetch | PASS | Upload and metadata work |
| File Upload | test_download_roundtrip | PASS | Download matches upload |
| File Upload | test_unsupported_extension_415 | PASS | Unsupported types rejected |
| File Upload | test_no_file_422 | PASS | Empty upload rejected |
| File Upload | test_oversize_stream_rejected_413 | PASS | Oversize files rejected |
| File Upload | test_missing_file_after_upload_404 | PASS | Missing files return 404 |
| File Upload | test_content_disposition_sanitized | PASS | Headers properly sanitized |
| Job Management | test_job_for_missing_input_404 | PASS | Missing input rejected |
| Job Management | test_client_only_conversion_rejected_422 | PASS | Client-only conversions blocked |
| Job Management | test_invalid_body_422 | PASS | Invalid bodies rejected |
| Job Management | test_cancel_missing_job_404 | PASS | Missing jobs return 404 |
| Job Management | test_jobs_list_empty_for_new_guest | PASS | Empty list for new guests |
| Rate Limiting | test_rate_limit_kicks_in | PASS | Rate limits enforced |
| End-to-End | test_markdown_to_pdf_end_to_end | PASS | Full conversion pipeline works |
| Quota | test_quota_shape | PASS | Quota endpoint correct |
| Cookie Security | test_guest_cookie_is_set_httponly | PASS | Cookie flags correct |
| Markdown | test_escapes_html_injection | PASS | XSS prevention works |
| Markdown | test_escapes_angle_brackets_inline | PASS | Angle brackets escaped |
| Markdown | test_bold_italic_code | PASS | Inline formatting works |
| Markdown | test_link_rendering | PASS | Links rendered correctly |
| Markdown | test_headings_and_lists | PASS | Headings and lists work |
| Markdown | test_document_skeleton | PASS | HTML skeleton correct |
| Catalog | test_detect_by_extension | PASS | Extension detection works |
| Catalog | test_detect_by_mime | PASS | MIME detection works |
| Catalog | test_find_conversion | PASS | Conversion lookup works |
| Catalog | test_extension_for | PASS | Extension mapping works |
| Content Disposition | test_ascii_quoted | PASS | ASCII filenames quoted |
| Content Disposition | test_crlf_stripped | PASS | CRLF injection prevented |
| Content Disposition | test_quotes_removed | PASS | Quotes removed from filenames |
| Content Disposition | test_unicode_rfc5987 | PASS | Unicode properly encoded |

## Summary

- **Total Tests**: 43
- **Passed**: 43
- **Failed**: 0
- **Regression**: None detected

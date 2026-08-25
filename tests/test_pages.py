from __future__ import annotations


class TestPages:
    def test_home_renders_html(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "Convert" in r.text
        # SEO essentials
        assert 'rel="canonical"' in r.text
        assert 'property="og:title"' in r.text
        assert "application/ld+json" in r.text
        # accessibility landmarks
        assert 'aria-label="Primary"' in r.text
        assert "Skip to content" in r.text

    def test_convert_page_embeds_catalog(self, client):
        r = client.get("/convert")
        assert r.status_code == 200
        assert "data-catalog" in r.text
        assert "Word to PDF" in r.text
        # catalog must expose "from" (not the pydantic field name "from_");
        # attribute values are HTML-entity escaped in the rendered page.
        catalog_attr = r.text.split("data-catalog")[1][:6000]
        assert "from_" not in catalog_attr
        assert "&#34;from&#34;" in catalog_attr

    def test_privacy_page(self, client):
        r = client.get("/privacy")
        assert r.status_code == 200
        assert "Privacy" in r.text

    def test_terms_page(self, client):
        r = client.get("/terms")
        assert r.status_code == 200
        assert "Terms of use" in r.text

    def test_unknown_page_returns_404_html(self, client):
        r = client.get("/definitely-not-a-page")
        assert r.status_code == 404
        assert "text/html" in r.headers["content-type"]
        assert "404" in r.text

    def test_unknown_api_path_returns_404_json(self, client):
        r = client.get("/api/v1/nope")
        assert r.status_code == 404
        assert "application/json" in r.headers["content-type"]

    def test_healthz(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_security_headers(self, client):
        r = client.get("/")
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_robots_txt(self, client):
        r = client.get("/robots.txt")
        assert r.status_code == 200
        assert "Sitemap:" in r.text
        assert "Disallow: /api/" in r.text

    def test_sitemap_xml(self, client):
        r = client.get("/sitemap.xml")
        assert r.status_code == 200
        assert "<urlset" in r.text
        assert "/convert" in r.text

    def test_favicon_served(self, client):
        r = client.get("/static/favicon.svg")
        assert r.status_code == 200
        assert "svg" in r.headers["content-type"]

    def test_theme_toggle_and_mobile_nav_present(self, client):
        html = client.get("/").text
        assert 'id="theme-toggle"' in html
        assert 'id="menu-toggle"' in html
        assert 'id="mobile-nav"' in html

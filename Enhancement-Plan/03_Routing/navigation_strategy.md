# Navigation Strategy

## Current Navigation

Server-rendered Jinja2 templates with a shared `base.html` layout. Navigation is static HTML in the base template.

### Pages

| Page | URL | Nav Priority |
|------|-----|-------------|
| Home | `/` | Primary |
| Converter | `/convert` | Primary |
| Privacy | `/privacy` | Footer |
| Terms | `/terms` | Footer |

### SEO Navigation

- `robots.txt`: Allow all, disallow `/api/`, includes sitemap reference
- `sitemap.xml`: All 4 pages with appropriate priorities (home=1.0, convert=0.9, privacy/terms=0.3)

## Changes in Enhancement

No navigation changes were made. All page routes, templates, and static assets remain unchanged.

### What Was NOT Changed

- Template structure (base.html, index.html, convert.html, etc.)
- Static CSS/JS files
- Menu/navigation HTML
- Page URL patterns
- 404 error page

## Notes

The navigation is minimal by design — this is a single-purpose tool with a linear flow: land -> convert -> download. No user accounts, no dashboard, no settings pages.

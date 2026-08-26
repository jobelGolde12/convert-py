# Build Analysis

## Build Command

No traditional build step required. The application uses:
- Raw CSS served from `/static/css/styles.css` (no preprocessor)
- Raw JavaScript from `/static/js/main.js` (no bundler)
- Python package built via Hatchling

## Static Asset Sizes

| Asset | Size | Notes |
|-------|------|-------|
| styles.css | ~19.5 KB | Single CSS file with design system |
| main.js | ~13.6 KB | Single JS file with theme, nav, converter |
| Total client JS | ~13.6 KB | No framework overhead |
| Total client CSS | ~19.5 KB | No framework overhead |

## Observations

- **No build step**: Eliminates build failures, reduces deployment complexity
- **Small payload**: Combined CSS + JS is ~33 KB uncompressed
- **Gzip compression**: SmartGzipMiddleware compresses text responses >=1KB
- **Cache headers**: Static files served with `Cache-Control: public, max-age=3600`
- **Google Fonts**: Inter loaded from Google Fonts CDN (external dependency)
- **No TypeScript**: Vanilla JS; type safety not applicable
- **No bundling**: Each file served individually; no tree-shaking needed

## Deployment Concerns

- Docker image includes LibreOffice (~300MB+), making it large
- SQLite used for development; production should use PostgreSQL
- Alembic migrations scaffolded but not generated yet

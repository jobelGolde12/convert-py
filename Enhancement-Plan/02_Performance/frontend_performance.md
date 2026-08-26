# Frontend Performance

## Scope

Frontend assets served by the convert-py application (Jinja2 templates, static CSS/JS). No frontend code changes were made in this enhancement cycle — all performance improvements are server-side.

## Server-Side Improvements Affecting Frontend

### 1. Pre-computed Catalog JSON

**File**: `app/main.py:199-204`

The `/convert` page template receives `catalog_json` — the full conversion catalog serialized to JSON. Previously computed on every request (serialized ~25 ConversionDef objects). Now computed once at startup.

```python
# Before (per-request)
def convert_page(request: Request):
    catalog = []
    for c in CONVERSIONS:
        item = c.model_dump()
        item["from"] = item.pop("from_")
        catalog.append(item)
    return templates.TemplateResponse(request, "convert.html",
        _template_context(request, catalog_json=json.dumps(catalog)...))

# After (startup only)
_catalog_items = []
for c in CONVERSIONS:
    item = c.model_dump()
    item["from"] = item.pop("from_")
    _catalog_items.append(item)
_catalog_json = json.dumps(_catalog_items).replace("</", "<\\/")
```

### 2. Gzip Compression

**File**: `app/main.py:34-92`

`SmartGzipMiddleware` compresses JSON and HTML responses >= 1KB for clients that accept gzip. Skips SSE streams and binary responses. This benefits all API responses and page renders.

### 3. Static Asset Caching

**File**: `app/main.py:95-105`

`CachedStaticFiles` sets `Cache-Control: public, max-age=3600` on all static assets (CSS, JS, favicon). Repeat visitors load from browser cache.

### 4. Streaming File Downloads

**File**: `app/api/routes/files.py:110-122`

File downloads use `StreamingResponse` instead of buffering the entire file in memory. This reduces TTFB for large files and avoids memory pressure.

## No Changes To

- Template rendering (Jinja2)
- CSS/JS assets
- Static asset bundling
- Image optimization

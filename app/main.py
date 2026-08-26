from __future__ import annotations

import gzip
import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.routes import files, formats, jobs, quota
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import AppError
from app.core.logger import setup_logging

logger = logging.getLogger("convert.request")

templates = Jinja2Templates(directory="app/templates")

# Content types worth compressing; SSE and binaries are excluded.
_GZIP_TYPES = ("application/json", "text/html", "text/plain", "text/css", "javascript", "xml")


class SmartGzipMiddleware:
    """Compress responses only when it is safe: skip streaming (SSE) responses.

    A response is considered non-streaming when it declares a Content-Length,
    which lets us buffer-compress without breaking event streams or chunked
    downloads. Responses below minimum_size pass through untouched.
    """

    def __init__(self, app: ASGIApp, minimum_size: int = 1024) -> None:
        self.app = app
        self.minimum_size = minimum_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        gzip_enabled = False
        accept_encoding = ""
        for name, value in scope.get("headers", []):
            if name == b"accept-encoding":
                accept_encoding = value.decode("latin-1")
                break
        wants_gzip = "gzip" in accept_encoding.lower()

        async def send_wrapper(message: Message) -> None:
            nonlocal gzip_enabled
            if message["type"] == "http.response.body" and gzip_enabled:
                message = {**message, "body": gzip.compress(message.get("body", b""))}
                await send(message)
                return
            if message["type"] != "http.response.start":
                await send(message)
                return

            headers_raw = message.get("headers", [])
            headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in headers_raw}
            content_type = headers.get("content-type", "")
            content_length = headers.get("content-length")

            compressible = any(t in content_type for t in _GZIP_TYPES)
            if (
                wants_gzip
                and compressible
                and content_length
                and int(content_length) >= self.minimum_size
            ):
                gzip_enabled = True
                new_headers = [
                    (k, v)
                    for k, v in headers_raw
                    if k.decode("latin-1").lower() != "content-length"
                ]
                new_headers.append((b"content-encoding", b"gzip"))
                new_headers.append((b"vary", b"Accept-Encoding"))
                message = {**message, "headers": new_headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)


class CachedStaticFiles(StaticFiles):
    """StaticFiles with a Cache-Control header for repeat-visit performance."""

    def __init__(self, *args: object, cache_max_age: int = 3600, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.cache_header = f"public, max-age={cache_max_age}"

    async def get_response(self, path: str, scope: Scope):  # type: ignore[override]
        response = await super().get_response(path, scope)
        response.headers.setdefault("Cache-Control", self.cache_header)
        return response


def _template_context(request: Request, **extra: object) -> dict[str, object]:
    base = {
        "request": request,
        "app_name": settings.app_name,
        "tagline": settings.tagline,
        "app_url": settings.app_url.rstrip("/"),
        "is_prod": settings.is_prod,
        "now_year": datetime.now(timezone.utc).year,
    }
    base.update(extra)
    return base


@asynccontextmanager
async def lifespan(application: FastAPI):
    if settings.is_prod:
        _validate_production_secrets()
    init_db()
    yield


def _validate_production_secrets() -> None:
    """Abort startup if critical secrets still have default values."""
    errors: list[str] = []
    if settings.secret_key in ("", "dev-secret-key-change-me"):
        errors.append("SECRET_KEY must be changed from its default value")
    if settings.upload_secret in ("", "dev-only-change-me"):
        errors.append("UPLOAD_SECRET must be changed from its default value")
    if errors:
        for e in errors:
            logger.error("FATAL: %s", e)
        sys.exit(1)


def create_app() -> FastAPI:
    setup_logging()
    application = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    origins = settings.cors_origins
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=bool(origins),
        allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        max_age=600,
    )
    application.add_middleware(SmartGzipMiddleware, minimum_size=1024)

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "method=%s path=%s status=%s duration_ms=%s request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        response.headers.setdefault("X-Request-ID", request_id)
        response.headers.setdefault("Server-Timing", f"app;dur={duration_ms}")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        if settings.is_prod:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    application.mount("/static", CachedStaticFiles(directory="app/static"), name="static")

    application.include_router(formats.router, prefix="/api/v1")
    application.include_router(quota.router, prefix="/api/v1")
    application.include_router(files.router, prefix="/api/v1/files")
    application.include_router(jobs.router, prefix="/api/v1/jobs")

    # ------------------------------------------------------------------ pages

    from app.core.conversions_catalog import CONVERSIONS, FORMATS

    server_conversions = [c for c in CONVERSIONS if c.location == "server"]

    # Pre-compute catalog JSON once at startup instead of per-request.
    _catalog_items = []
    for c in CONVERSIONS:
        item = c.model_dump()
        item["from"] = item.pop("from_")
        _catalog_items.append(item)
    _catalog_json = json.dumps(_catalog_items).replace("</", "<\\/")

    @application.get("/")
    def home(request: Request):
        return templates.TemplateResponse(
            request,
            "index.html",
            _template_context(
                request,
                conversions=server_conversions,
                formats=FORMATS,
            ),
        )

    @application.get("/convert")
    def convert_page(request: Request):
        return templates.TemplateResponse(
            request,
            "convert.html",
            _template_context(
                request,
                catalog_json=_catalog_json,
                anon_limit=settings.anon_conversions_per_day,
            ),
        )

    @application.get("/privacy")
    def privacy_page(request: Request):
        return templates.TemplateResponse(request, "privacy.html", _template_context(request))

    @application.get("/terms")
    def terms_page(request: Request):
        return templates.TemplateResponse(request, "terms.html", _template_context(request))

    @application.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @application.get("/robots.txt")
    def robots_txt():
        base = settings.app_url.rstrip("/")
        return Response(
            content=f"User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {base}/sitemap.xml\n",
            media_type="text/plain",
        )

    @application.get("/sitemap.xml")
    def sitemap_xml():
        base = settings.app_url.rstrip("/")
        pages = [("", "1.0"), ("/convert", "0.9"), ("/privacy", "0.3"), ("/terms", "0.3")]
        entries = "\n".join(
            f"  <url><loc>{base}{path}</loc><priority>{priority}</priority></url>"
            for path, priority in pages
        )
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n"
        )
        return Response(content=xml, media_type="application/xml")

    # ------------------------------------------------------------- error pages

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422, content={"error": "INVALID_DATA", "message": str(exc.errors()[:3])}
        )

    async def not_found_handler(request: Request, exc) -> object:
        if request.url.path.startswith(("/api/", "/static/")):
            return JSONResponse(
                status_code=404, content={"error": "NOT_FOUND", "message": "Not found"}
            )
        return templates.TemplateResponse(
            request, "404.html", _template_context(request), status_code=404
        )

    application.add_exception_handler(404, not_found_handler)

    return application


app = create_app()

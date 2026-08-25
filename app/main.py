from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import files, formats, jobs, quota
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import AppError
from app.core.logger import setup_logging

templates = Jinja2Templates(directory="app/templates")


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
    init_db()
    yield


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

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
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

    application.mount("/static", StaticFiles(directory="app/static"), name="static")

    application.include_router(formats.router, prefix="/api/v1")
    application.include_router(quota.router, prefix="/api/v1")
    application.include_router(files.router, prefix="/api/v1/files")
    application.include_router(jobs.router, prefix="/api/v1/jobs")

    # ------------------------------------------------------------------ pages

    from app.core.conversions_catalog import CONVERSIONS, FORMATS

    server_conversions = [c for c in CONVERSIONS if c.location == "server"]

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
        import json

        catalog = []
        for c in CONVERSIONS:
            item = c.model_dump()
            item["from"] = item.pop("from_")
            catalog.append(item)

        return templates.TemplateResponse(
            request,
            "convert.html",
            _template_context(
                request,
                catalog_json=json.dumps(catalog).replace("</", "<\\/"),
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

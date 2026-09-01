from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from app.config import settings
from app.db import init_db
from app.redis_client import close_redis
from app.routes import router
from app.routes_account import router as account_router
from app.storage import get_storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_redis()


def _origin_allowed(origin: str | None) -> str | None:
    if not origin or origin == "null":
        return None
    allowed = set(settings.cors_origins or [])
    allowed.add(settings.web_app_url.rstrip("/"))
    if settings.is_development():
        return origin
    if origin.rstrip("/") in allowed:
        return origin
    if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
        return origin if settings.is_development() else None
    return None


class CorsMiddleware(BaseHTTPMiddleware):
    """Development: permissive. Production: allowlist from CORS_ORIGINS + WEB_APP_URL."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        allow_origin = _origin_allowed(origin)
        if settings.is_development() and not allow_origin:
            allow_origin = origin or "*"

        if request.method == "OPTIONS":
            req_headers = request.headers.get("access-control-request-headers") or "*"
            headers = {
                "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
                "Access-Control-Allow-Headers": req_headers,
                "Access-Control-Max-Age": "600",
                "Vary": "Origin",
            }
            if allow_origin:
                headers["Access-Control-Allow-Origin"] = allow_origin
            return PlainTextResponse("ok", status_code=200, headers=headers)

        response: Response = await call_next(request)
        if allow_origin:
            response.headers["Access-Control-Allow-Origin"] = allow_origin
        response.headers["Vary"] = "Origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CorsMiddleware)
app.include_router(router, prefix="/api")
app.include_router(account_router, prefix="/api")

# Local creative files are always written to disk; mount even when R2 is the primary store.
app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")
app.mount("/generated", StaticFiles(directory=str(settings.generated_dir)), name="generated")
app.mount("/previews", StaticFiles(directory=str(settings.previews_dir), html=True), name="previews")


@app.get("/assets/{key:path}")
async def serve_stored_asset(key: str):
    """Serve R2 (or other remote) assets when R2_PUBLIC_URL is not configured."""
    storage = get_storage()
    if not storage.exists(key):
        raise HTTPException(status_code=404, detail="Asset not found")
    data = await storage.read_bytes(key)
    lower = key.lower()
    if lower.endswith(".png"):
        media_type = "image/png"
    elif lower.endswith(".jpg") or lower.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif lower.endswith(".webp"):
        media_type = "image/webp"
    elif lower.endswith(".html"):
        media_type = "text/html"
    else:
        media_type = "application/octet-stream"
    return Response(content=data, media_type=media_type)


@app.get("/")
async def root():
    return {
        "name": "AdzMate Campaign Auto-Pilot",
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/api/health",
    }
